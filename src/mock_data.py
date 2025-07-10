import json
import random
from datetime import datetime, timedelta
from typing import List, Dict


def generate_mock_azure_devops_data():
    """Generate mock Azure DevOps work items data for flow metrics calculation"""

    # Team members from the evaluation files
    team_members = [
        "Ian Abellana",
        "Glizzel Ann Artates",
        "Joshua Asi",
        "Prince Joedymar Jud Barro",
        "Jude Marco Bayot",
        "Ian Belmonte",
        "Patrick Oniel Bernardo",
        "Erwin Biglang-awa",
        "Antonio Florencio Bisquera",
        "Janiel Apollo Bodiongan",
        "Ronald Bucayan",
        "James Aaron Constantino",
        "Ariel Dimapilis",
        "Nymar Fernandez",
        "Jay Mark Lagmay",
        "Nenissa Malibago",
        "Christian Nailat",
        "Christopher Reyes",
        "Christopher Jan Riños",
        "Joebert Rosales",
        "Rex Nino Santos",
        "Diego Saylon",
        "Myra Selda",
        "Joyce Diane Sison",
        "Cleo Erika Soriano",
        "Rio Alyssa Venturina",
    ]

    work_item_types = ["User Story", "Bug", "Task", "Feature"]
    states = ["New", "Active", "Resolved", "Closed"]
    priorities = ["Critical", "High", "Medium", "Low"]

    work_items = []
    base_date = datetime(2024, 1, 1)

    for i in range(200):  # Generate 200 work items
        created_date = base_date + timedelta(days=random.randint(0, 200))

        # Generate state transitions
        state_transitions = []
        current_date = created_date

        # New -> Active
        if random.random() > 0.1:  # 90% get activated
            active_date = current_date + timedelta(days=random.randint(0, 5))
            state_transitions.append(
                {
                    "state": "Active",
                    "date": active_date.isoformat(),
                    "assigned_to": random.choice(team_members),
                }
            )
            current_date = active_date

            # Active -> Resolved
            if random.random() > 0.2:  # 80% get resolved
                resolved_date = current_date + timedelta(days=random.randint(1, 14))
                state_transitions.append(
                    {
                        "state": "Resolved",
                        "date": resolved_date.isoformat(),
                        "assigned_to": random.choice(team_members),
                    }
                )
                current_date = resolved_date

                # Resolved -> Closed
                if random.random() > 0.1:  # 90% get closed
                    closed_date = current_date + timedelta(days=random.randint(0, 3))
                    state_transitions.append(
                        {
                            "state": "Closed",
                            "date": closed_date.isoformat(),
                            "assigned_to": random.choice(team_members),
                        }
                    )

        work_item = {
            "id": f"WI-{i+1:04d}",
            "title": f"Work Item {i+1}",
            "type": random.choice(work_item_types),
            "priority": random.choice(priorities),
            "created_date": created_date.isoformat(),
            "created_by": random.choice(team_members),
            "assigned_to": random.choice(team_members),
            "current_state": (
                state_transitions[-1]["state"] if state_transitions else "New"
            ),
            "state_transitions": state_transitions,
            "story_points": random.randint(1, 8) if random.random() > 0.3 else None,
            "effort_hours": random.randint(2, 40) if random.random() > 0.2 else None,
            "tags": random.sample(
                ["frontend", "backend", "database", "api", "ui", "testing"],
                random.randint(1, 3),
            ),
        }

        work_items.append(work_item)

    return work_items


def save_mock_data():
    """Save mock data to JSON file"""
    mock_data = generate_mock_azure_devops_data()

    with open("mock_azure_devops_workitems.json", "w") as f:
        json.dump(mock_data, f, indent=2)

    print(f"Generated {len(mock_data)} mock work items")
    return mock_data


if __name__ == "__main__":
    save_mock_data()
