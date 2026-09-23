class RWDesign:
    def __init__(self, dcp_path):
        from pyrapidwright import setup_rw
        setup_rw()
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
        Everything is validated first, since generating the ILA core runs Vivado and takes minutes.
        """
        from com.xilinx.rapidwright.debug import ILAInserter

        if not 1 <= len(nets_to_probe) <= 1024:
            raise ValueError(f"Probe count must be between 1 and 1024, got {len(nets_to_probe)}")
        if probe_depth not in (1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072):
            raise ValueError(f"Unsupported probe depth {probe_depth}, must be a power of two from 1024 to 131072")
        missing = [n for n in [*nets_to_probe, clk_net_name] if self.netlist.getHierNetFromName(n) is None]
        if missing:
            raise ValueError("Nets not found in design: " + ", ".join(missing))

        probe_count = len(nets_to_probe)
        print(f"[*] Creating ILA design for {probe_count} probes (depth: {probe_depth})...")

        # Create ILA design using Vivado (via RapidWright)
        ila_design = ILAInserter.createILADesign(probe_count, probe_depth, self.design.getPart())

        # Apply ILA core to design (instantiates module and connects clock)
        print(f"[*] Applying ILA to design and connecting clock: {clk_net_name}")
        ILAInserter.applyILAToDesign(self.design, ila_design, clk_net_name)

        # The ILA sits in the top cell and exposes one bus port, probes[N-1:0]
        ila_cell_inst = self.design.getModuleInst(ila_design.getName()).getCellInst()

        print("[*] Connecting probes...")
        for i, net_name in enumerate(nets_to_probe):
            self._net_to_top(net_name, f"ila_probe{i}").createPortInst(f"probes[{i}]", ila_cell_inst)
            print(f"    [+] Connected {net_name} to probes[{i}]")

    def _net_to_top(self, net_name, port_name):
        """
        Returns a top-level EDIFNet carrying net_name, adding an output port named port_name
        at each level of hierarchy on the way up. Mirrors the clock handling in
        RapidWright's ILAInserter.applyILAToDesign.
        """
        from com.xilinx.rapidwright.edif import EDIFDirection, EDIFHierNet

        hier_net = self.netlist.getHierNetFromName(net_name)
        # Start from the alias of this net closest to the top
        for alias in self.netlist.getNetAliases(hier_net):
            if alias.getHierarchicalInst().getDepth() < hier_net.getHierarchicalInst().getDepth():
                hier_net = alias
        # ponytail: ports go on the cell *type*, so a type instantiated more than once gets the port
        # on every instance (the others are left unconnected), same as upstream's clock handling
        while not hier_net.getHierarchicalInst().isTopLevelInst():
            inst = hier_net.getHierarchicalInst()
            port = inst.getCellType().createPort(port_name, EDIFDirection.OUTPUT, 1)
            hier_net.getNet().createPortInst(port)
            parent = inst.getParent()
            hier_net = EDIFHierNet(parent, parent.getCellType().createNet(port_name))
            hier_net.getNet().createPortInst(port, inst.getInst())
        return hier_net.getNet()

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