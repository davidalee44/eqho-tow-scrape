# Workflow Builder Documentation

## Overview

The Workflow Builder is a React Flow-based visual interface for creating outreach sequences. It allows users to build complex multi-step workflows by dragging and connecting nodes.

## Architecture

Built using [React Flow](https://reactflow.dev/), inspired by [play.reactflow.dev](https://play.reactflow.dev/).

### Components

- **WorkflowBuilder**: Main component that orchestrates the workflow
- **Node Components**: Individual node types (Email, SMS, Phone, Delay, Condition, Start, End)
- **Property Panels**: Inline editing for node properties

## Node Types

### 1. Start Node
- **Type**: `start`
- **Purpose**: Entry point for the workflow
- **Properties**: None
- **Outputs**: 1 (to next step)

### 2. Email Node
- **Type**: `email`
- **Purpose**: Send email to company
- **Properties**:
  - `subject`: Email subject line
  - `template`: Email body template (supports Jinja2 variables)
- **Outputs**: 1 (to next step)

### 3. SMS Node
- **Type**: `sms`
- **Purpose**: Send SMS to company
- **Properties**:
  - `template`: SMS message template (supports Jinja2 variables)
- **Outputs**: 1 (to next step)

### 4. Phone Node
- **Type**: `phone`
- **Purpose**: Trigger phone call via Eqho.ai
- **Properties**:
  - `template`: Phone script template (supports Jinja2 variables)
- **Outputs**: 1 (to next step)

### 5. Delay Node
- **Type**: `delay`
- **Purpose**: Add delay between steps
- **Properties**:
  - `delay_hours`: Number of hours to wait
- **Outputs**: 1 (to next step)

### 6. Condition Node
- **Type**: `condition`
- **Purpose**: Branch workflow based on conditions
- **Properties**:
  - `field`: Company field to check (e.g., "has_impound_service")
  - `operator`: Comparison operator ("equals", "contains", "greater_than", "less_than")
  - `value`: Value to compare against
- **Outputs**: 2 ("Yes" path and "No" path)

### 7. End Node
- **Type**: `end`
- **Purpose**: Exit point for the workflow
- **Properties**: None
- **Inputs**: 1 (from previous step)

## Workflow Data Structure

```typescript
interface WorkflowData {
  name: string;
  description?: string;
  is_active: boolean;
  steps: WorkflowStep[];
}

interface WorkflowStep {
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
```

## API Integration

### Save Workflow

```typescript
POST /api/v1/outreach/sequences
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Follow-up Sequence",
  "description": "Email then SMS follow-up",
  "is_active": true,
  "steps": [
    {
      "channel": "email",
      "delay_hours": 0,
      "template": "Hi {{company.name}}, ...",
      "subject": "Partnership Opportunity"
    },
    {
      "channel": "delay",
      "delay_hours": 24
    },
    {
      "channel": "sms",
      "delay_hours": 0,
      "template": "Hi {{company.name}}, following up..."
    }
  ]
}
```

### Load Workflow

```typescript
GET /api/v1/outreach/sequences/{sequence_id}
Authorization: Bearer {token}
```

## Usage Examples

### Simple Email Sequence

1. Add Start node
2. Add Email node
3. Connect Start → Email
4. Configure Email node (subject, template)
5. Add Delay node
6. Connect Email → Delay
7. Configure Delay (24 hours)
8. Add another Email node
9. Connect Delay → Email
10. Connect Email → End

### Conditional Branching

1. Add Start node
2. Add Email node
3. Add Condition node
4. Connect Start → Email → Condition
5. Configure Condition (e.g., `has_impound_service == true`)
6. Add Phone node (Yes path)
7. Add SMS node (No path)
8. Connect Condition "Yes" → Phone
9. Connect Condition "No" → SMS
10. Connect both to End node

## Template Variables

Templates support Jinja2 syntax with company data:

- `{{company.name}}` - Company name
- `{{company.phone_primary}}` - Primary phone
- `{{company.email}}` - Email address
- `{{company.address_city}}` - City
- `{{company.has_impound_service}}` - Impound service flag
- `{{company.rating}}` - Google rating

Example:
```
Hi {{company.name}},

I noticed your towing company in {{company.address_city}} offers impound services.
We'd love to partner with you!

Best regards,
TowPilot Team
```

## Features

### Visual Editing
- Drag nodes to reposition
- Connect nodes by dragging from output to input handles
- Click nodes to edit properties
- Delete nodes (except Start/End)

### Real-time Preview
- See node previews as you configure them
- Visual feedback for selected nodes
- Animated connections

### Save/Load
- Save workflows to backend
- Load existing workflows
- Auto-save (optional)

### Validation
- Ensure workflow starts with Start node
- Ensure workflow ends with End node
- Validate node connections
- Check for required properties

## Styling

Nodes use gradient backgrounds for visual distinction:
- **Start**: Purple gradient
- **End**: Pink gradient
- **Email**: Blue gradient
- **SMS**: Green gradient
- **Phone**: Orange gradient
- **Delay**: Peach gradient
- **Condition**: Teal gradient

## Development

### Setup

```bash
cd frontend
npm install
npm run dev
```

### Building

```bash
npm run build
```

### Testing

The workflow builder can be tested by:
1. Creating a workflow visually
2. Saving it to the backend
3. Loading it back
4. Verifying the sequence executes correctly

## Future Enhancements

- [ ] Undo/Redo functionality
- [ ] Copy/Paste nodes
- [ ] Workflow templates
- [ ] Visual validation indicators
- [ ] Export/Import workflows (JSON)
- [ ] Workflow versioning
- [ ] A/B testing support
- [ ] Analytics integration
- [ ] Real-time collaboration

