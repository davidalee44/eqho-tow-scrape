import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

const ConditionNode: React.FC<NodeProps> = ({ data, selected }) => {
  const condition = data.condition || { field: '', operator: 'equals', value: '' };
  const conditionText = condition.field
    ? `${condition.field} ${condition.operator} ${condition.value}`
    : 'Set condition';

  return (
    <div className={`condition-node ${selected ? 'selected' : ''}`}>
      <div className="condition-node-content">
        <div className="condition-node-icon">🔀</div>
        <div className="condition-node-label">{data.label || 'Condition'}</div>
        <div className="condition-node-text">{conditionText}</div>
      </div>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} id="true" label="Yes" />
      <Handle type="source" position={Position.Right} id="false" label="No" />
    </div>
  );
};

export default ConditionNode;

