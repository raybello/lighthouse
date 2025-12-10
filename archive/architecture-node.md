``` mermaid
sequenceDiagram 
    autonumber

    User->>NodeEditor: Create Node ❌
    Note over User,NodeEditor: GUI Interaction <br/>Add node to graph

    User->>NodeEditor: Create Edge ❌
    Note over User,NodeEditor: GUI Interaction <br/>Add edge to graph

    NodeEditor->>ExecEngine: Execute Nodes ❌
    Note over NodeEditor,ExecEngine: Iterate over nodes <br/>after Topological Sort


    loop NodeInputs Ready 
        ExecEngine->>ExecEngine: Execute node function ❌
    end


```

# Legend

- ❌ - Not implemented
- ✅ - Completed & Implemented

## Execution Flow
✅- Execution is triggered from node(NID)
✅- Callback on UI is triggered
✅- Application performs sort to determine execution order
✅- Create an execution with the Executor, with ordered nodes (and execution levels in next release)
❌- Iterate through nodes, execute once for each input items a node has
❌- Receive node input item and resolve field values from context into state struct
❌- call execute() on node after state has been seeded, add return value of execute() to output item of current node
❌- propagate output items to all children nodes
❌- execute next node until completed



