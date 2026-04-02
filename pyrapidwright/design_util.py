# Delay imports until JVM is started
def _get_java_classes():
    from com.xilinx.rapidwright.design import Design, Module, ModuleInst
    from com.xilinx.rapidwright.device import Device
    from com.xilinx.rapidwright.debug import ILAInserter
    from com.xilinx.rapidwright.edif import EDIFDirection
    return Design, Module, ModuleInst, Device, ILAInserter, EDIFDirection

class RWDesign:
    def __init__(self, dcp_path):
        from com.xilinx.rapidwright.design import Design
        try:
            self.design = Design.readCheckpoint(dcp_path)
        except Exception as e:
            msg = str(e)
            if "sl_iport" in msg or "Couldn't find EDIFPort" in msg:
                raise RuntimeError(
                    "RapidWright Limitation: Failed to load DCP because it already contains a Debug Hub (ILA). "
                    "Incremental ILA insertion is not supported. Please start from a clean DCP and add all probes in one pass."
                ) from e
            raise
        self.device = self.design.getDevice()
        self.netlist = self.design.getNetlist()

    def get_all_nets(self, include_static=False):
        """Returns a list of nets, optionally filtering VCC/GND."""
        nets = list(self.design.getNets())
        if not include_static:
            return [n for n in nets if not n.isStaticNet()]
        return nets

    def get_net_from_name(self, name):
        """Finds a net by its hierarchical name."""
        return self.design.getNet(name)

    def get_placed_instances(self):
        """Returns only instances that have a physical location on the FPGA."""
        return [i for i in self.design.getInstances() if i.isPlaced()]

    def get_logical_instances(self):
        """Returns all instances in the netlist (logical level)."""
        return list(self.netlist.getAllInstances())

    def insert_ila(self, nets_to_probe, clk_net_name, probe_depth=1024):
        """
        Inserts an ILA with probes connected to the specified nets.
        """
        Design, Module, ModuleInst, Device, ILAInserter, EDIFDirection = _get_java_classes()
        
        probe_count = len(nets_to_probe)
        print(f"[*] Creating ILA design for {probe_count} probes (depth: {probe_depth})...")
        
        # Create ILA design using Vivado (via RapidWrite)
        ila_design = ILAInserter.createILADesign(probe_count, probe_depth, self.design.getPart())
        
        # Apply ILA core to design (instantiates module and connects clock)
        print(f"[*] Applying ILA to design and connecting clock: {clk_net_name}")
        ILAInserter.applyILAToDesign(self.design, ila_design, clk_net_name)
        
        # Connect probes
        ila_inst = self.design.getModuleInst(ila_design.getName())
        ila_cell_inst = ila_inst.getCellInst()
        
        print("[*] Connecting probes...")
        for i, net_name in enumerate(nets_to_probe):
            net = self.design.getNet(net_name)
            if not net:
                print(f"[!] Warning: Could not find net {net_name}")
                continue
                
            port_name = f"probe{i}"
            edif_net = net.getLogicalNet()
            if edif_net:
                edif_net.createPortInst(port_name, ila_cell_inst)
                print(f"    [+] Connected {net_name} to {port_name}")
            else:
                print(f"    [!] Warning: Net {net_name} has no logical net.")

    def save(self, dcp_path):
        """Saves the design to a DCP file."""
        self.design.writeCheckpoint(dcp_path)

    def get_net_info(self, net_name):
        """
        Returns detailed information about a net.
        """
        hier_net = self.design.getNetlist().getHierNetFromName(net_name)
        if not hier_net:
            return None
            
        info = {
            "name": str(hier_net.getHierarchicalNetName()),
            "drivers": [],
            "loads": []
        }
        
        # Get leaf pins connected to this net
        for hier_port_inst in hier_net.getLeafHierPortInsts(True, True):
            pin_name = str(hier_port_inst.getPortInst().getName())
            cell_name = str(hier_port_inst.getFullHierarchicalInstName())
            
            direction = str(hier_port_inst.getPortInst().getDirection())
            if "INPUT" in direction.upper():
                info["loads"].append(f"{cell_name}/{pin_name}")
            else:
                info["drivers"].append(f"{cell_name}/{pin_name}")
                
        return info

    def get_cell_info(self, cell_name):
        """
        Returns information about a cell instance.
        """
        hier_cell = self.design.getNetlist().getHierCellInstFromName(cell_name)
        if not hier_cell:
            return None
            
        info = {
            "name": str(hier_cell.getFullHierarchicalInstName()),
            "type": str(hier_cell.getInst().getCellType().getName()),
            "pins": [str(p.getName()) for p in hier_cell.getInst().getPortInsts()]
        }
        
        # Try to find physical placement
        phys_cell = self.design.getCell(cell_name)
        if phys_cell:
            info["site"] = str(phys_cell.getSite().getName()) if phys_cell.getSite() else "UNPLACED"
            info["tile"] = str(phys_cell.getTile().getName()) if phys_cell.getTile() else "UNPLACED"
            
        return info