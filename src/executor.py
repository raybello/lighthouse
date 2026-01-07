from .nodes import *

class Executor(object): 
    def __init__(self):
        self.execution_array = []
        self.execution = {}
        self.node_inputs = {}
        self.node_outputs = {}
        self.connections = {}

    def set_node_input(self, id, item):
        if id in self.node_inputs:
            self.node_inputs[id].append(item)

    def set_node_output(self, id, item):
        if id in self.node_outputs:
            self.node_outputs[id].append(item)

    def set_exec_status(self, node_id, color, status):
        self.nodes[node_id].status = status
        dpg.set_value(item=f"{node_id}_exec_status", value=status)
        dpg.configure_item(
            item=f"{node_id}_exec_status",
            color=color,
        )
        if status == "RUNNING":
            dpg.configure_item(
                item=f"{node_id}_loading",
                show=True,
                color=color,
            )
        else:
            dpg.configure_item(item=f"{node_id}_loading", show=False)

    def create_execution(self, nodes, connections, triggered_by):
        self.execution = {
            "id": str(uuid.uuid4())[-8:],
            "nodes": nodes,
            "connections": connections,
            "inputs": {},
            "outputs": {},
            "createdAt": time.time(),
            "endedAt": None,
            "triggeredBy": triggered_by,
            "traces":[]
        }
        self.connections = connections
        console.print("Created Execution")
        console.print(self.execution)
        console.print(self.connections)
        self.begin_execution()

    def end_execution(self):
        self.execution['endedAt'] = time.time()
        self.execution["inputs"] = self.node_inputs
        self.execution["outputs"] = self.node_outputs
        self.execution_array.append(self.execution)
        console.print(self.execution_array)

    def begin_execution(self):
        console.print("Starting Execution")
        nodes = self.execution['nodes']
        for node in nodes:
            console.print(node)
