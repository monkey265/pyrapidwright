"""
Checks the Java-backed logic against a tiny netlist built in RapidWright (no DCP or Vivado needed):

    top: BUFG -> clk -> FDRE ff_top, LUT1 lut
         u_sub (cell "sub"): FDRE ff -> net q      (q only exists inside the hierarchy)

Run: uv run python tests/test_design.py
"""
import tempfile
from pathlib import Path

from pyrapidwright import setup_rw
from pyrapidwright.design_util import RWDesign
from pyrapidwright.analysis import get_clock_nets, report_resource_usage

PART = "xc7a35tcpg236-1"


def make_design():
    setup_rw()
    from com.xilinx.rapidwright.design import Design, Unisim
    from com.xilinx.rapidwright.edif import EDIFCell

    d = Design("t", PART)
    netlist = d.getNetlist()
    top = netlist.getTopCell()
    prim = netlist.getHDIPrimitive

    bufg = top.createChildCellInst("bufg", prim(Unisim.BUFG))
    ff_top = top.createChildCellInst("ff_top", prim(Unisim.FDRE))
    top.createChildCellInst("lut", prim(Unisim.LUT1))
    clk = top.createNet("clk")
    clk.createPortInst("O", bufg)
    clk.createPortInst("C", ff_top)

    sub = EDIFCell(netlist.getWorkLibrary(), "sub")
    ff = sub.createChildCellInst("ff", prim(Unisim.FDRE))
    sub.createNet("q").createPortInst("Q", ff)
    top.createChildCellInst("u_sub", sub)

    dcp = Path(tempfile.mkdtemp()) / "t.dcp"
    d.writeCheckpoint(str(dcp))
    return RWDesign(str(dcp))


def test_resource_usage(design):
    counts = report_resource_usage(design)
    assert (counts["LUTs"], counts["Registers"], counts["Others"]) == (1, 2, 1), counts


def test_clock_nets_come_from_bufg(design):
    assert get_clock_nets(design) == ["clk"]


def test_insert_ila_rejects_unknown_nets_before_vivado(design):
    try:
        design.insert_ila(["u_sub/q", "nope"], "clk")
    except ValueError as e:
        assert "nope" in str(e) and "u_sub/q" not in str(e), e
    else:
        raise AssertionError("expected ValueError")


def test_net_to_top_punches_port_up_hierarchy(design):
    top_net = design._net_to_top("u_sub/q", "ila_probe0")
    top = design.netlist.getTopCell()
    assert top_net.getParentCell().equals(top)
    # the new top-level net connects to the new output port on u_sub, which is driven by q inside
    assert any(str(p.getName()) == "ila_probe0" and p.getCellInst() is not None for p in top_net.getPortInsts())
    sub_q = design.netlist.getHierNetFromName("u_sub/q").getNet()
    assert any(str(p.getName()) == "ila_probe0" and p.getCellInst() is None for p in sub_q.getPortInsts())


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(make_design())  # fresh design per test: _net_to_top mutates the netlist
            print(f"ok  {name}")
