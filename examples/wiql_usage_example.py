"""Example usage of WIQL filtering capabilities."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.exceptions import WIQLError, WIQLValidationError
from src.wiql_client import WIQLClient, create_wiql_client_from_config
from src.wiql_parser import (
    WIQLParser,
    create_basic_work_items_query,
    create_filtered_work_items_query,
)
from src.wiql_transformer import TransformationConfig, WIQLTransformer


def example_basic_wiql_usage():
    """Example of basic WIQL usage."""
    print("=== Basic WIQL Usage Example ===")

    # Create a WIQL client (replace with your actual configuration)
    client = WIQLClient(
        org_url="https://dev.azure.com/your-org",
        project="your-project",
        pat_token="your-pat-token",
    )

    # Test connection and WIQL capabilities
    print("\n1. Testing WIQL connection...")
    test_result = client.test_wiql_connection()
    print(f"Connection test result: {test_result['message']}")

    if test_result["wiql_ok"]:
        print("✓ WIQL functionality is working")
    else:
        print("✗ WIQL functionality has issues")
        return

    # Get WIQL capabilities
    print("\n2. Getting WIQL capabilities...")
    capabilities = client.get_wiql_capabilities()
    print(f"WIQL enabled: {capabilities['wiql_enabled']}")
    print(f"Supported field types: {capabilities.get('field_types', [])}")
    print(f"Supported operators: {capabilities.get('supported_operators', [])}")

    # Example 1: Basic work items query
    print("\n3. Basic work items query...")
    try:
        work_items = client.get_work_items_with_wiql(
            days_back=30,
            work_item_types=["User Story", "Bug"],
            states=["Active", "Resolved"],
        )
        print(f"Found {len(work_items)} work items")

        # Display first few items
        for item in work_items[:3]:
            print(
                f"  - {item['id']}: {item['title']} ({item['type']}) - {item['current_state']}"
            )

    except Exception as e:
        print(f"Error: {e}")


def example_custom_wiql_queries():
    """Example of custom WIQL queries."""
    print("\n=== Custom WIQL Queries Example ===")

    client = WIQLClient(
        org_url="https://dev.azure.com/your-org",
        project="your-project",
        pat_token="your-pat-token",
    )

    # Example 1: Work items by priority
    print("\n1. High priority work items...")
    high_priority_query = """
    SELECT [System.Id], [System.Title], [System.State], [Microsoft.VSTS.Common.Priority]
    FROM WorkItems
    WHERE [System.TeamProject] = 'your-project'
    AND [Microsoft.VSTS.Common.Priority] <= 2
    AND [System.State] <> 'Closed'
    ORDER BY [Microsoft.VSTS.Common.Priority] ASC, [System.CreatedDate] DESC
    """

    try:
        # Validate query first
        validation_result = client.validate_wiql_query(high_priority_query)
        if validation_result["valid"]:
            print("✓ Query is valid")

            # Execute query
            work_items = client.execute_wiql_query(high_priority_query)
            print(f"Found {len(work_items)} high priority work items")

        else:
            print("✗ Query validation failed:")
            for error in validation_result["errors"]:
                print(f"  - {error}")

    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Work items by assignee
    print("\n2. Work items by specific assignee...")
    assignee_query = """
    SELECT [System.Id], [System.Title], [System.AssignedTo]
    FROM WorkItems
    WHERE [System.TeamProject] = 'your-project'
    AND [System.AssignedTo] = 'John Doe'
    AND [System.State] IN ('Active', 'Committed', 'In Progress')
    ORDER BY [System.CreatedDate] DESC
    """

    try:
        work_items = client.execute_wiql_query(assignee_query)
        print(f"Found {len(work_items)} work items assigned to John Doe")

    except Exception as e:
        print(f"Error: {e}")

    # Example 3: Work items with specific tags
    print("\n3. Work items with specific tags...")
    tags_query = """
    SELECT [System.Id], [System.Title], [System.Tags]
    FROM WorkItems
    WHERE [System.TeamProject] = 'your-project'
    AND [System.Tags] CONTAINS 'critical'
    ORDER BY [System.CreatedDate] DESC
    """

    try:
        work_items = client.execute_wiql_query(tags_query)
        print(f"Found {len(work_items)} work items with 'critical' tag")

    except Exception as e:
        print(f"Error: {e}")


def example_wiql_parser_usage():
    """Example of WIQL parser usage."""
    print("\n=== WIQL Parser Usage Example ===")

    parser = WIQLParser()

    # Example 1: Parse a WIQL query
    print("\n1. Parsing a WIQL query...")
    query_string = """
    SELECT [System.Id], [System.Title], [System.State]
    FROM WorkItems
    WHERE [System.TeamProject] = 'MyProject'
    AND [System.WorkItemType] IN ('User Story', 'Bug')
    AND [System.State] <> 'Closed'
    ORDER BY [System.CreatedDate] DESC
    """

    try:
        parsed_query = parser.parse_query(query_string)
        print(f"✓ Query parsed successfully")
        print(f"  - Select fields: {parsed_query.select_fields}")
        print(f"  - From clause: {parsed_query.from_clause}")
        print(f"  - Number of conditions: {len(parsed_query.where_conditions)}")
        print(f"  - Project filter: {parsed_query.project_filter}")
        print(f"  - Order by: {parsed_query.order_by}")

        # Validate the parsed query
        validation_errors = parser.validate_query(parsed_query)
        if validation_errors:
            print("✗ Query validation failed:")
            for error in validation_errors:
                print(f"  - {error}")
        else:
            print("✓ Query validation passed")

            # Convert back to WIQL string
            regenerated_query = parsed_query.to_wiql_string()
            print(f"\nRegenerated WIQL:\n{regenerated_query}")

    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Build a query programmatically
    print("\n2. Building a query programmatically...")
    try:
        built_query = parser.build_query_for_work_items(
            project="MyProject",
            days_back=30,
            work_item_types=["User Story", "Bug", "Task"],
            states=["Active", "Committed", "In Progress"],
            assignees=["John Doe", "Jane Smith"],
            additional_filters={
                "Microsoft.VSTS.Common.Priority": ["1", "2"],
                "System.Tags": "urgent",
            },
        )

        print("✓ Query built successfully")
        query_string = built_query.to_wiql_string()
        print(f"Generated WIQL:\n{query_string}")

    except Exception as e:
        print(f"Error: {e}")


def example_wiql_transformer_usage():
    """Example of WIQL transformer usage."""
    print("\n=== WIQL Transformer Usage Example ===")

    # Sample raw work item data (as returned from Azure DevOps API)
    raw_work_items = [
        {
            "id": 1,
            "fields": {
                "System.Title": "Implement user authentication",
                "System.WorkItemType": "User Story",
                "System.State": "Active",
                "System.CreatedDate": "2023-01-01T10:00:00Z",
                "System.AssignedTo": {"displayName": "John Doe"},
                "Microsoft.VSTS.Common.Priority": 1,
                "Microsoft.VSTS.Scheduling.StoryPoints": 8.0,
                "System.Tags": "backend;security;sprint1",
                "System.AreaPath": "MyProject\\Backend",
                "System.IterationPath": "MyProject\\Sprint 1",
            },
        },
        {
            "id": 2,
            "fields": {
                "System.Title": "Fix login page styling",
                "System.WorkItemType": "Bug",
                "System.State": "Resolved",
                "System.CreatedDate": "2023-01-02T11:00:00Z",
                "System.ClosedDate": "2023-01-03T15:30:00Z",
                "System.AssignedTo": {"displayName": "Jane Smith"},
                "Microsoft.VSTS.Common.Priority": 2,
                "System.Tags": "frontend;bug;sprint1",
                "System.AreaPath": "MyProject\\Frontend",
                "System.IterationPath": "MyProject\\Sprint 1",
            },
        },
    ]

    # Create transformer with configuration
    config = TransformationConfig(
        include_custom_fields=True, validate_data=True, fill_missing_values=True
    )
    transformer = WIQLTransformer(config)

    try:
        # Transform raw data to WorkItem models
        print("\n1. Transforming raw work items...")
        work_items = transformer.transform_work_items(raw_work_items)

        print(f"✓ Transformed {len(work_items)} work items")

        # Display transformed data
        for work_item in work_items:
            print(f"\nWork Item {work_item.id}:")
            print(f"  Title: {work_item.title}")
            print(f"  Type: {work_item.type}")
            print(f"  State: {work_item.state}")
            print(f"  Assigned to: {work_item.assigned_to}")
            print(f"  Priority: {work_item.priority}")
            print(f"  Effort: {work_item.effort}")
            print(f"  Tags: {work_item.tags}")
            print(f"  Sprint: {work_item.sprint_name}")
            print(f"  Created: {work_item.created_date}")
            print(f"  Closed: {work_item.closed_date}")
            if work_item.closed_date:
                print(f"  Lead time: {work_item.lead_time_days:.1f} days")

        # Validate transformed data
        print("\n2. Validating transformed data...")
        validation_errors = transformer.validate_transformed_data(work_items)
        if validation_errors:
            print("✗ Validation failed:")
            for error in validation_errors:
                print(f"  - {error}")
        else:
            print("✓ Validation passed")

        # Get transformation summary
        print("\n3. Transformation summary...")
        summary = transformer.get_transformation_summary(work_items)
        print(f"  Total items: {summary['total_items']}")
        print(f"  By type: {summary['by_type']}")
        print(f"  By state: {summary['by_state']}")
        print(f"  Items with effort: {summary['with_effort']}")
        print(f"  Items with assignee: {summary['with_assignee']}")
        print(f"  Completed items: {summary['completed_items']}")

        # Transform to metrics format
        print("\n4. Converting to metrics format...")
        metrics_data = transformer.transform_to_metrics_format(work_items)
        print(f"✓ Converted {len(metrics_data)} items to metrics format")

        # Display first item in metrics format
        if metrics_data:
            print(f"Sample metrics item:")
            sample_item = metrics_data[0]
            for key, value in sample_item.items():
                print(f"  {key}: {value}")

    except Exception as e:
        print(f"Error: {e}")


def example_wiql_statistics():
    """Example of WIQL statistics functionality."""
    print("\n=== WIQL Statistics Example ===")

    client = WIQLClient(
        org_url="https://dev.azure.com/your-org",
        project="your-project",
        pat_token="your-pat-token",
    )

    try:
        # Get overall statistics
        print("\n1. Getting overall work item statistics...")
        stats = client.get_work_item_statistics()

        print(f"Total work items: {stats['total_items']}")
        print(f"By type: {stats['by_type']}")
        print(f"By state: {stats['by_state']}")
        print(f"By assignee: {stats['by_assignee']}")

        if stats["date_range"]["earliest"] and stats["date_range"]["latest"]:
            print(
                f"Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}"
            )

        # Get statistics with custom query
        print("\n2. Getting statistics for active work items...")
        active_query = """
        SELECT [System.Id], [System.WorkItemType], [System.State], [System.AssignedTo]
        FROM WorkItems
        WHERE [System.TeamProject] = 'your-project'
        AND [System.State] IN ('Active', 'Committed', 'In Progress')
        """

        active_stats = client.get_work_item_statistics(active_query)
        print(f"Active work items: {active_stats['total_items']}")
        print(f"Active by type: {active_stats['by_type']}")
        print(f"Active by assignee: {active_stats['by_assignee']}")

    except Exception as e:
        print(f"Error: {e}")


def example_wiql_custom_fields():
    """Example of working with custom fields in WIQL."""
    print("\n=== WIQL Custom Fields Example ===")

    client = WIQLClient(
        org_url="https://dev.azure.com/your-org",
        project="your-project",
        pat_token="your-pat-token",
    )

    # Register custom fields
    print("\n1. Registering custom fields...")
    try:
        client.register_custom_field(
            "Custom.BusinessValue",
            "integer",
            display_name="Business Value",
            is_sortable=True,
        )

        client.register_custom_field(
            "Custom.CustomerImpact",
            "string",
            display_name="Customer Impact",
            is_sortable=False,
        )

        print("✓ Custom fields registered")

        # Get updated field list
        fields = client.get_supported_fields()
        print(f"Total supported fields: {len(fields)}")

        # Show custom fields
        custom_fields = {k: v for k, v in fields.items() if k.startswith("Custom.")}
        print(f"Custom fields: {list(custom_fields.keys())}")

    except Exception as e:
        print(f"Error: {e}")

    # Use custom fields in query
    print("\n2. Querying with custom fields...")
    try:
        custom_query = """
        SELECT [System.Id], [System.Title], [Custom.BusinessValue], [Custom.CustomerImpact]
        FROM WorkItems
        WHERE [System.TeamProject] = 'your-project'
        AND [Custom.BusinessValue] >= 50
        ORDER BY [Custom.BusinessValue] DESC
        """

        # Validate query with custom fields
        validation_result = client.validate_wiql_query(custom_query)
        if validation_result["valid"]:
            print("✓ Custom field query is valid")

            # Execute query
            work_items = client.execute_wiql_query(custom_query)
            print(f"Found {len(work_items)} high business value items")

        else:
            print("✗ Custom field query validation failed:")
            for error in validation_result["errors"]:
                print(f"  - {error}")

    except Exception as e:
        print(f"Error: {e}")


def example_error_handling():
    """Example of error handling in WIQL operations."""
    print("\n=== WIQL Error Handling Example ===")

    client = WIQLClient(
        org_url="https://dev.azure.com/your-org",
        project="your-project",
        pat_token="your-pat-token",
    )

    # Example 1: Invalid WIQL query
    print("\n1. Testing invalid WIQL query...")
    try:
        invalid_query = "SELECT [Unknown.Field] FROM WorkItems"
        client.execute_wiql_query(invalid_query, validate=True)
    except WIQLValidationError as e:
        print(f"✓ Caught validation error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    # Example 2: Malformed WIQL syntax
    print("\n2. Testing malformed WIQL syntax...")
    try:
        malformed_query = "INVALID WIQL SYNTAX"
        client.execute_wiql_query(malformed_query, validate=True)
    except WIQLError as e:
        print(f"✓ Caught WIQL error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    # Example 3: Query validation without execution
    print("\n3. Testing query validation...")
    test_queries = [
        "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = 'test'",  # Valid
        "SELECT [Unknown.Field] FROM WorkItems",  # Invalid field
        "SELECT [System.Id] FROM WorkItems WHERE [System.Id] LIKE 'test'",  # Invalid operator for field type
    ]

    for i, query in enumerate(test_queries, 1):
        try:
            validation_result = client.validate_wiql_query(query)
            if validation_result["valid"]:
                print(f"  Query {i}: ✓ Valid")
            else:
                print(f"  Query {i}: ✗ Invalid - {validation_result['errors'][0]}")
        except Exception as e:
            print(f"  Query {i}: ✗ Error - {e}")


def main():
    """Main function to run all examples."""
    print("WIQL Usage Examples")
    print("==================")
    print(
        "Note: Replace 'your-org', 'your-project', and 'your-pat-token' with actual values"
    )

    # Run examples (commented out to avoid actual API calls)
    # example_basic_wiql_usage()
    # example_custom_wiql_queries()
    example_wiql_parser_usage()
    example_wiql_transformer_usage()
    # example_wiql_statistics()
    # example_wiql_custom_fields()
    example_error_handling()

    print("\n" + "=" * 50)
    print("Examples completed!")
    print("For actual usage, uncomment the API-dependent examples")
    print("and provide valid Azure DevOps configuration.")


if __name__ == "__main__":
    main()
