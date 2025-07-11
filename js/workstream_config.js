/**
 * Workstream Configuration - JavaScript Fallback
 *
 * This file provides embedded workstream configuration for offline usage
 * or when the JSON config file cannot be fetched.
 *
 * This configuration matches exactly with config/workstream_config.json
 * and implements the same Power BI SWITCH logic patterns.
 */

window.WORKSTREAM_CONFIG = {
  "workstreams": {
    "Data": {
      "description": "Data analytics and engineering team",
      "name_patterns": [
        "Nenissa",
        "Ariel",
        "Patrick Oniel",
        "Kennedy Oliveira",
        "Christopher Jan",
        "Jegs",
        "Ian Belmonte"
      ]
    },
    "QA": {
      "description": "Quality assurance and testing team",
      "name_patterns": [
        "Sharon",
        "Lorenz",
        "Arvin"
      ]
    },
    "OutSystems": {
      "description": "OutSystems development team",
      "name_patterns": [
        "Apollo",
        "Glizzel",
        "Prince",
        "Patrick Russel",
        "Rio",
        "Nymar"
      ]
    }
  },
  "default_workstream": "Others",
  "matching_options": {
    "case_sensitive": false,
    "partial_match": true,
    "match_full_name": false
  }
};

// Configuration version and metadata
window.WORKSTREAM_CONFIG_META = {
  version: "1.0.0",
  updated: "2024-01-20",
  source: "Embedded JavaScript fallback",
  description: "Power BI equivalent workstream configuration for browser-only dashboards"
};

console.log('Workstream configuration fallback loaded');
