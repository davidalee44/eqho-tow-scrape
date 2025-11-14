# TowPilot Workflow Builder

A React Flow-based visual workflow builder for creating outreach sequences.

## Features

- **Visual Workflow Builder**: Drag-and-drop interface for building outreach sequences
- **Multiple Node Types**: Email, SMS, Phone, Delay, and Condition nodes
- **Real-time Preview**: See your workflow as you build it
- **Save/Load**: Persist workflows to the backend API
- **Node Properties Panel**: Configure each node's properties inline

## Installation

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Building

```bash
npm run build
```

## Usage

1. **Add Nodes**: Click the toolbar buttons to add different node types
2. **Connect Nodes**: Drag from one node's output handle to another node's input handle
3. **Configure Nodes**: Click on a node to see its properties panel on the right
4. **Save Workflow**: Enter a workflow name and click "Save Workflow"

## Node Types

### Start Node
- Entry point for the workflow
- Cannot be deleted

### End Node
- Exit point for the workflow
- Cannot be deleted

### Email Node
- Sends an email to the company
- Properties: Subject, Template

### SMS Node
- Sends an SMS to the company
- Properties: Message Template

### Phone Node
- Triggers a phone call via Eqho.ai
- Properties: Script Template

### Delay Node
- Adds a delay between steps
- Properties: Delay in hours

### Condition Node
- Branches the workflow based on conditions
- Properties: Field, Operator, Value
- Has two output paths: "Yes" and "No"

## API Integration

The workflow builder integrates with the backend API at `/api/v1/outreach/sequences`:

- **POST** `/api/v1/outreach/sequences` - Create a new workflow
- **GET** `/api/v1/outreach/sequences` - List all workflows

Make sure your backend is running and accessible at `http://localhost:8000` (or configure the proxy in `vite.config.ts`).

## Based on React Flow

This workflow builder is built using [React Flow](https://reactflow.dev/), inspired by the examples at [play.reactflow.dev](https://play.reactflow.dev/).

