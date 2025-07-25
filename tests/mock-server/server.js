const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 8080;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Mock Azure DevOps API endpoints
app.get('/:organization/_apis/wit/wiql', (req, res) => {
  const mockResponse = {
    queryType: "flat",
    queryResultType: "workItem",
    asOf: new Date().toISOString(),
    columns: [
      { referenceName: "System.Id", name: "ID", url: "https://localhost/fields/System.Id" },
      { referenceName: "System.Title", name: "Title", url: "https://localhost/fields/System.Title" },
      { referenceName: "System.State", name: "State", url: "https://localhost/fields/System.State" }
    ],
    sortColumns: [
      { field: { referenceName: "System.Id", name: "ID" }, descending: false }
    ],
    workItems: [
      { id: 1, url: "https://localhost/workItems/1" },
      { id: 2, url: "https://localhost/workItems/2" },
      { id: 3, url: "https://localhost/workItems/3" }
    ]
  };
  res.json(mockResponse);
});

app.post('/:organization/_apis/wit/wiql', (req, res) => {
  const { query } = req.body;

  // Simulate different responses based on query
  if (query.includes('System.WorkItemType = \'Bug\'')) {
    res.json({
      queryType: "flat",
      queryResultType: "workItem",
      asOf: new Date().toISOString(),
      workItems: [
        { id: 10, url: "https://localhost/workItems/10" },
        { id: 11, url: "https://localhost/workItems/11" }
      ]
    });
  } else {
    res.json({
      queryType: "flat",
      queryResultType: "workItem",
      asOf: new Date().toISOString(),
      workItems: [
        { id: 1, url: "https://localhost/workItems/1" },
        { id: 2, url: "https://localhost/workItems/2" },
        { id: 3, url: "https://localhost/workItems/3" }
      ]
    });
  }
});

// Get work items batch
app.post('/:organization/_apis/wit/workitemsbatch', (req, res) => {
  const { ids } = req.body;
  const workItems = ids.map(id => ({
    id: id,
    rev: 1,
    fields: {
      "System.Id": id,
      "System.Title": `Work Item ${id}`,
      "System.State": id % 2 === 0 ? "Done" : "In Progress",
      "System.WorkItemType": "User Story",
      "System.CreatedDate": "2024-01-01T00:00:00Z",
      "System.ChangedDate": new Date().toISOString(),
      "Microsoft.VSTS.Common.StateChangeDate": new Date().toISOString(),
      "Microsoft.VSTS.Scheduling.StoryPoints": Math.floor(Math.random() * 8) + 1
    },
    relations: [],
    url: `https://localhost/workItems/${id}`
  }));

  res.json({ count: workItems.length, value: workItems });
});

// Get single work item
app.get('/:organization/_apis/wit/workitems/:id', (req, res) => {
  const { id } = req.params;
  res.json({
    id: parseInt(id),
    rev: 1,
    fields: {
      "System.Id": parseInt(id),
      "System.Title": `Work Item ${id}`,
      "System.State": parseInt(id) % 2 === 0 ? "Done" : "In Progress",
      "System.WorkItemType": "User Story",
      "System.CreatedDate": "2024-01-01T00:00:00Z",
      "System.ChangedDate": new Date().toISOString(),
      "Microsoft.VSTS.Common.StateChangeDate": new Date().toISOString(),
      "Microsoft.VSTS.Scheduling.StoryPoints": Math.floor(Math.random() * 8) + 1
    },
    relations: [],
    url: `https://localhost/workItems/${id}`
  });
});

// Projects endpoint
app.get('/:organization/_apis/projects', (req, res) => {
  res.json({
    count: 2,
    value: [
      {
        id: "project-1",
        name: "Test Project 1",
        description: "Test project for unit tests",
        url: "https://localhost/projects/project-1",
        state: "wellFormed"
      },
      {
        id: "project-2",
        name: "Test Project 2",
        description: "Another test project",
        url: "https://localhost/projects/project-2",
        state: "wellFormed"
      }
    ]
  });
});

// Teams endpoint
app.get('/:organization/_apis/projects/:projectId/teams', (req, res) => {
  res.json({
    count: 1,
    value: [
      {
        id: "team-1",
        name: "Development Team",
        url: "https://localhost/teams/team-1",
        description: "Main development team"
      }
    ]
  });
});

// Error simulation endpoints
app.get('/error/500', (req, res) => {
  res.status(500).json({ error: 'Internal Server Error' });
});

app.get('/error/401', (req, res) => {
  res.status(401).json({ error: 'Unauthorized' });
});

app.get('/error/timeout', (req, res) => {
  // Simulate timeout - don't respond
  setTimeout(() => {
    res.status(408).json({ error: 'Request Timeout' });
  }, 30000);
});

// Catch-all for unimplemented endpoints
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Mock endpoint not implemented: ${req.method} ${req.originalUrl}`
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Mock Azure DevOps API server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});

module.exports = app;
