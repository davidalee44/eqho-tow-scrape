import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

const SMSNode: React.FC<NodeProps> = ({ data, selected }) => {
  return (
    <div className={`sms-node ${selected ? 'selected' : ''}`}>
      <div className="sms-node-content">
        <div className="sms-node-icon">💬</div>
        <div className="sms-node-label">{data.label || 'SMS'}</div>
        {data.template && (
          <div className="sms-node-preview">
            {data.template.substring(0, 30)}...
          </div>
        )}
      </div>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default SMSNode;

