import React, { useCallback, useMemo, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Connection,
  NodeTypes,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

import EmailNode from './nodes/EmailNode';
import SMSNode from './nodes/SMSNode';
import PhoneNode from './nodes/PhoneNode';
import StartNode from './nodes/StartNode';
import EndNode from './nodes/EndNode';
import DelayNode from './nodes/DelayNode';
import ConditionNode from './nodes/ConditionNode';

import './WorkflowBuilder.css';
import './nodes/nodes.css';

// Define node types
const nodeTypes: NodeTypes = {
  start: StartNode,
  email: EmailNode,
  sms: SMSNode,
  phone: PhoneNode,
  delay: DelayNode,
  condition: ConditionNode,
  end: EndNode,
};

export interface WorkflowStep {
  id: string;
  type: 'email' | 'sms' | 'phone' | 'delay' | 'condition';
  channel?: 'email' | 'sms' | 'phone';
  delay_hours?: number;
  template?: string;
  subject?: string;
  condition?: {
    field: string;
    operator: string;
    value: string;
  };
  position: { x: number; y: number };
}

export interface WorkflowData {
  name: string;
  description?: string;
  is_active: boolean;
  steps: WorkflowStep[];
}

interface WorkflowBuilderProps {
  initialData?: WorkflowData;
  onSave?: (data: WorkflowData) => void;
  onLoad?: () => Promise<WorkflowData | null>;
  apiBaseUrl?: string;
}

const WorkflowBuilder: React.FC<WorkflowBuilderProps> = ({
  initialData,
  onSave,
  onLoad,
  apiBaseUrl = '/api/v1',
}) => {
  const [workflowName, setWorkflowName] = useState(initialData?.name || '');
  const [workflowDescription, setWorkflowDescription] = useState(
    initialData?.description || ''
  );
  const [isActive, setIsActive] = useState(initialData?.is_active ?? true);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  // Initialize nodes from initial data or create default start/end nodes
  const initialNodes: Node[] = useMemo(() => {
    if (initialData?.steps && initialData.steps.length > 0) {
      return initialData.steps.map((step, index) => ({
        id: step.id,
        type: step.type,
        position: step.position,
        data: {
          label: step.type === 'email' ? 'Email' : step.type === 'sms' ? 'SMS' : step.type === 'phone' ? 'Phone' : step.type === 'delay' ? 'Delay' : 'Condition',
          channel: step.channel,
          delay_hours: step.delay_hours,
          template: step.template,
          subject: step.subject,
          condition: step.condition,
          onUpdate: (data: any) => {
            setNodes((nds) =>
              nds.map((node) =>
                node.id === step.id ? { ...node, data: { ...node.data, ...data } } : node
              )
            );
          },
        },
      }));
    }
    return [
      {
        id: 'start-1',
        type: 'start',
        position: { x: 250, y: 100 },
        data: { label: 'Start' },
      },
      {
        id: 'end-1',
        type: 'end',
        position: { x: 250, y: 600 },
        data: { label: 'End' },
      },
    ];
  }, [initialData]);

  const initialEdges: Edge[] = useMemo(() => {
    if (initialData?.steps && initialData.steps.length > 1) {
      const edges: Edge[] = [];
      for (let i = 0; i < initialData.steps.length - 1; i++) {
        edges.push({
          id: `e${initialData.steps[i].id}-${initialData.steps[i + 1].id}`,
          source: initialData.steps[i].id,
          target: initialData.steps[i + 1].id,
          type: 'smoothstep',
          animated: true,
          markerEnd: {
            type: MarkerType.ArrowClosed,
          },
        });
      }
      return edges;
    }
    return [];
  }, [initialData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge({ ...params, animated: true, markerEnd: { type: MarkerType.ArrowClosed } }, eds));
    },
    [setEdges]
  );

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const addNode = useCallback(
    (type: 'email' | 'sms' | 'phone' | 'delay' | 'condition') => {
      const newNode: Node = {
        id: `${type}-${Date.now()}`,
        type,
        position: {
          x: Math.random() * 400 + 200,
          y: Math.random() * 400 + 200,
        },
        data: {
          label: type === 'email' ? 'Email' : type === 'sms' ? 'SMS' : type === 'phone' ? 'Phone' : type === 'delay' ? 'Delay' : 'Condition',
          channel: type !== 'delay' && type !== 'condition' ? type : undefined,
          delay_hours: type === 'delay' ? 24 : undefined,
          template: '',
          subject: type === 'email' ? '' : undefined,
          onUpdate: (data: any) => {
            setNodes((nds) =>
              nds.map((node) =>
                node.id === newNode.id ? { ...node, data: { ...node.data, ...data } } : node
              )
            );
          },
        },
      };
      setNodes((nds) => [...nds, newNode]);
    },
    [setNodes]
  );

  const deleteNode = useCallback(() => {
    if (selectedNode && selectedNode.type !== 'start' && selectedNode.type !== 'end') {
      setNodes((nds) => nds.filter((node) => node.id !== selectedNode.id));
      setEdges((eds) =>
        eds.filter(
          (edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id
        )
      );
      setSelectedNode(null);
    }
  }, [selectedNode, setNodes, setEdges]);

  const convertToWorkflowData = useCallback((): WorkflowData => {
    // Sort nodes by their position in the flow (top to bottom)
    const sortedNodes = [...nodes]
      .filter((node) => node.type !== 'start' && node.type !== 'end')
      .sort((a, b) => a.position.y - b.position.y);

    const steps: WorkflowStep[] = sortedNodes.map((node) => {
      const step: WorkflowStep = {
        id: node.id,
        type: node.type as 'email' | 'sms' | 'phone' | 'delay' | 'condition',
        position: node.position,
      };

      if (node.type === 'email' || node.type === 'sms' || node.type === 'phone') {
        step.channel = node.data.channel || node.type;
        step.template = node.data.template || '';
        if (node.type === 'email') {
          step.subject = node.data.subject || '';
        }
      }

      if (node.type === 'delay') {
        step.delay_hours = node.data.delay_hours || 24;
      }

      if (node.type === 'condition') {
        step.condition = node.data.condition;
      }

      return step;
    });

    return {
      name: workflowName,
      description: workflowDescription,
      is_active: isActive,
      steps,
    };
  }, [nodes, workflowName, workflowDescription, isActive]);

  const handleSave = useCallback(async () => {
    const workflowData = convertToWorkflowData();
    
    if (onSave) {
      onSave(workflowData);
    } else {
      // Default API save
      try {
        const response = await fetch(`${apiBaseUrl}/outreach/sequences`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify({
            name: workflowData.name,
            description: workflowData.description,
            is_active: workflowData.is_active,
            steps: workflowData.steps.map((step) => ({
              channel: step.channel,
              delay_hours: step.delay_hours,
              template: step.template,
              subject: step.subject,
            })),
          }),
        });

        if (response.ok) {
          alert('Workflow saved successfully!');
        } else {
          throw new Error('Failed to save workflow');
        }
      } catch (error) {
        console.error('Error saving workflow:', error);
        alert('Failed to save workflow');
      }
    }
  }, [convertToWorkflowData, onSave, apiBaseUrl]);

  const handleLoad = useCallback(async () => {
    if (onLoad) {
      const data = await onLoad();
      if (data) {
        setWorkflowName(data.name);
        setWorkflowDescription(data.description || '');
        setIsActive(data.is_active);
        // Reload nodes and edges from data
        // This would require re-initializing the flow
      }
    }
  }, [onLoad]);

  return (
    <div className="workflow-builder">
      <div className="workflow-builder-header">
        <div className="workflow-builder-title">
          <h2>Outreach Workflow Builder</h2>
        </div>
        <div className="workflow-builder-controls">
          <input
            type="text"
            placeholder="Workflow Name"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="workflow-name-input"
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={workflowDescription}
            onChange={(e) => setWorkflowDescription(e.target.value)}
            className="workflow-description-input"
          />
          <label className="workflow-active-toggle">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
            />
            Active
          </label>
          <button onClick={handleSave} className="save-button">
            Save Workflow
          </button>
          {onLoad && (
            <button onClick={handleLoad} className="load-button">
              Load Workflow
            </button>
          )}
        </div>
      </div>

      <div className="workflow-builder-toolbar">
        <button onClick={() => addNode('email')} className="toolbar-button">
          📧 Add Email
        </button>
        <button onClick={() => addNode('sms')} className="toolbar-button">
          💬 Add SMS
        </button>
        <button onClick={() => addNode('phone')} className="toolbar-button">
          📞 Add Phone
        </button>
        <button onClick={() => addNode('delay')} className="toolbar-button">
          ⏱️ Add Delay
        </button>
        <button onClick={() => addNode('condition')} className="toolbar-button">
          🔀 Add Condition
        </button>
        {selectedNode && selectedNode.type !== 'start' && selectedNode.type !== 'end' && (
          <button onClick={deleteNode} className="toolbar-button delete-button">
            🗑️ Delete Selected
          </button>
        )}
      </div>

      <div className="workflow-builder-content">
        <div className="react-flow-container">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            className="react-flow-wrapper"
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>

        {selectedNode && (
          <div className="node-properties-panel">
            <h3>Node Properties</h3>
            <div className="node-properties-content">
              {selectedNode.type === 'email' && (
                <EmailNodeProperties node={selectedNode} />
              )}
              {selectedNode.type === 'sms' && (
                <SMSNodeProperties node={selectedNode} />
              )}
              {selectedNode.type === 'phone' && (
                <PhoneNodeProperties node={selectedNode} />
              )}
              {selectedNode.type === 'delay' && (
                <DelayNodeProperties node={selectedNode} />
              )}
              {selectedNode.type === 'condition' && (
                <ConditionNodeProperties node={selectedNode} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Property panels for each node type
const EmailNodeProperties: React.FC<{ node: Node }> = ({ node }) => {
  const [subject, setSubject] = useState(node.data.subject || '');
  const [template, setTemplate] = useState(node.data.template || '');

  const handleUpdate = () => {
    if (node.data.onUpdate) {
      node.data.onUpdate({ subject, template });
    }
  };

  return (
    <div>
      <label>
        Subject:
        <input
          type="text"
          value={subject}
          onChange={(e) => {
            setSubject(e.target.value);
            handleUpdate();
          }}
          onBlur={handleUpdate}
        />
      </label>
      <label>
        Template:
        <textarea
          value={template}
          onChange={(e) => {
            setTemplate(e.target.value);
            handleUpdate();
          }}
          onBlur={handleUpdate}
          rows={10}
        />
      </label>
    </div>
  );
};

const SMSNodeProperties: React.FC<{ node: Node }> = ({ node }) => {
  const [template, setTemplate] = useState(node.data.template || '');

  const handleUpdate = () => {
    if (node.data.onUpdate) {
      node.data.onUpdate({ template });
    }
  };

  return (
    <div>
      <label>
        Message Template:
        <textarea
          value={template}
          onChange={(e) => {
            setTemplate(e.target.value);
            handleUpdate();
          }}
          onBlur={handleUpdate}
          rows={10}
        />
      </label>
    </div>
  );
};

const PhoneNodeProperties: React.FC<{ node: Node }> = ({ node }) => {
  const [template, setTemplate] = useState(node.data.template || '');

  const handleUpdate = () => {
    if (node.data.onUpdate) {
      node.data.onUpdate({ template });
    }
  };

  return (
    <div>
      <label>
        Script Template:
        <textarea
          value={template}
          onChange={(e) => {
            setTemplate(e.target.value);
            handleUpdate();
          }}
          onBlur={handleUpdate}
          rows={10}
        />
      </label>
    </div>
  );
};

const DelayNodeProperties: React.FC<{ node: Node }> = ({ node }) => {
  const [delayHours, setDelayHours] = useState(node.data.delay_hours || 24);

  const handleUpdate = () => {
    if (node.data.onUpdate) {
      node.data.onUpdate({ delay_hours: delayHours });
    }
  };

  return (
    <div>
      <label>
        Delay (hours):
        <input
          type="number"
          value={delayHours}
          onChange={(e) => {
            setDelayHours(parseInt(e.target.value) || 0);
            handleUpdate();
          }}
          onBlur={handleUpdate}
          min={0}
        />
      </label>
    </div>
  );
};

const ConditionNodeProperties: React.FC<{ node: Node }> = ({ node }) => {
  const [condition, setCondition] = useState(
    node.data.condition || { field: '', operator: 'equals', value: '' }
  );

  const handleUpdate = () => {
    if (node.data.onUpdate) {
      node.data.onUpdate({ condition });
    }
  };

  return (
    <div>
      <label>
        Field:
        <input
          type="text"
          value={condition.field}
          onChange={(e) => {
            setCondition({ ...condition, field: e.target.value });
            handleUpdate();
          }}
          onBlur={handleUpdate}
        />
      </label>
      <label>
        Operator:
        <select
          value={condition.operator}
          onChange={(e) => {
            setCondition({ ...condition, operator: e.target.value });
            handleUpdate();
          }}
        >
          <option value="equals">Equals</option>
          <option value="contains">Contains</option>
          <option value="greater_than">Greater Than</option>
          <option value="less_than">Less Than</option>
        </select>
      </label>
      <label>
        Value:
        <input
          type="text"
          value={condition.value}
          onChange={(e) => {
            setCondition({ ...condition, value: e.target.value });
            handleUpdate();
          }}
          onBlur={handleUpdate}
        />
      </label>
    </div>
  );
};

export default WorkflowBuilder;

