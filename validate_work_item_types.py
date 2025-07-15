#!/usr/bin/env python3
"""
Work Item Types Validation Tool

Validates work item type configuration against actual data
and provides coverage analysis.
"""

import json
import sys
import os
from typing import Dict, List, Set, Any
from collections import Counter
from src.work_item_type_mapper import create_type_mapper


def load_work_items_data(data_path: str) -> List[Dict[str, Any]]:
    """Load work items data from JSON file"""
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Work items data file not found: {data_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in data file: {e}")


def extract_types_from_data(work_items: List[Dict[str, Any]]) -> Dict[str, int]:
    """Extract work item types and their counts from data"""
    types = [item.get('type', 'Unknown') for item in work_items if 'type' in item]
    return dict(Counter(types))


def validate_type_coverage(config_types: Set[str], data_types: Set[str]) -> Dict[str, Any]:
    """Validate type coverage between configuration and data"""
    
    # Types in both config and data
    covered_types = config_types.intersection(data_types)
    
    # Types in data but not in config
    missing_from_config = data_types - config_types
    
    # Types in config but not in data
    missing_from_data = config_types - data_types
    
    coverage_percentage = (len(covered_types) / len(data_types)) * 100 if data_types else 0
    
    return {
        'total_data_types': len(data_types),
        'total_config_types': len(config_types),
        'covered_types': len(covered_types),
        'coverage_percentage': coverage_percentage,
        'covered_type_list': sorted(list(covered_types)),
        'missing_from_config': sorted(list(missing_from_config)),
        'missing_from_data': sorted(list(missing_from_data))
    }


def validate_volume_accuracy(config_volumes: Dict[str, int], data_volumes: Dict[str, int]) -> Dict[str, Any]:
    """Validate volume accuracy between configuration and actual data"""
    
    validation_results = {}
    total_data_items = sum(data_volumes.values())
    
    for type_name, config_count in config_volumes.items():
        data_count = data_volumes.get(type_name, 0)
        
        # Calculate percentage from data
        data_percentage = (data_count / total_data_items) * 100 if total_data_items > 0 else 0
        
        # Check accuracy
        count_accurate = config_count == data_count
        percentage_diff = abs(data_percentage - config_count) if isinstance(config_count, (int, float)) else None
        
        validation_results[type_name] = {
            'config_count': config_count,
            'data_count': data_count,
            'count_accurate': count_accurate,
            'count_difference': data_count - config_count,
            'data_percentage': round(data_percentage, 1),
            'percentage_difference': round(percentage_diff, 1) if percentage_diff is not None else None
        }
    
    return validation_results


def analyze_ranking_accuracy(mapper, data_volumes: Dict[str, int]) -> Dict[str, Any]:
    """Analyze ranking accuracy between configuration and data"""
    
    # Get actual ranking from data
    data_ranking = sorted(data_volumes.items(), key=lambda x: x[1], reverse=True)
    actual_ranks = {type_name: rank + 1 for rank, (type_name, _) in enumerate(data_ranking)}
    
    ranking_analysis = {}
    
    for type_name in mapper.get_all_types():
        config = mapper.get_type_config(type_name)
        if config and type_name in actual_ranks:
            config_rank = config.volume['rank']
            actual_rank = actual_ranks[type_name]
            rank_difference = actual_rank - config_rank
            
            ranking_analysis[type_name] = {
                'config_rank': config_rank,
                'actual_rank': actual_rank,
                'rank_difference': rank_difference,
                'rank_accurate': rank_difference == 0
            }
    
    return ranking_analysis


def validate_calculation_rules(mapper, data_types: Set[str]) -> Dict[str, Any]:
    """Validate calculation rules against available data types"""
    
    calc_rules = mapper.get_calculation_rules()
    validation = {}
    
    for rule_name, rule_config in calc_rules.items():
        include_types = set(rule_config.get('include_types', []))
        exclude_types = set(rule_config.get('exclude_types', []))
        
        # Check if included types exist in data
        missing_include_types = include_types - data_types
        
        # Check if excluded types exist in data  
        present_exclude_types = exclude_types.intersection(data_types)
        
        validation[rule_name] = {
            'include_types_count': len(include_types),
            'exclude_types_count': len(exclude_types),
            'missing_include_types': sorted(list(missing_include_types)),
            'present_exclude_types': sorted(list(present_exclude_types)),
            'include_coverage': len(include_types - missing_include_types) / len(include_types) * 100 if include_types else 100
        }
    
    return validation


def generate_validation_report(
    coverage_result: Dict[str, Any],
    volume_validation: Dict[str, Any], 
    ranking_analysis: Dict[str, Any],
    calculation_validation: Dict[str, Any],
    data_volumes: Dict[str, int]
) -> str:
    """Generate comprehensive validation report"""
    
    report = []
    report.append("=" * 80)
    report.append("WORK ITEM TYPES VALIDATION REPORT")
    report.append("=" * 80)
    
    # Coverage Summary
    report.append(f"\n📊 TYPE COVERAGE SUMMARY")
    report.append(f"   ├── Total types in data: {coverage_result['total_data_types']}")
    report.append(f"   ├── Total types in config: {coverage_result['total_config_types']}")
    report.append(f"   ├── Covered types: {coverage_result['covered_types']}")
    report.append(f"   └── Coverage percentage: {coverage_result['coverage_percentage']:.1f}%")
    
    # Missing types
    if coverage_result['missing_from_config']:
        report.append(f"\n❌ TYPES MISSING FROM CONFIG ({len(coverage_result['missing_from_config'])}):")
        for type_name in coverage_result['missing_from_config']:
            count = data_volumes.get(type_name, 0)
            percentage = (count / sum(data_volumes.values())) * 100
            report.append(f"   ├── {type_name}: {count} items ({percentage:.1f}%)")
    
    if coverage_result['missing_from_data']:
        report.append(f"\n⚠️  TYPES IN CONFIG BUT NOT IN DATA ({len(coverage_result['missing_from_data'])}):")
        for type_name in coverage_result['missing_from_data']:
            report.append(f"   ├── {type_name}")
    
    # Volume Accuracy
    report.append(f"\n📈 VOLUME ACCURACY ANALYSIS")
    accurate_counts = sum(1 for v in volume_validation.values() if v['count_accurate'])
    total_types = len(volume_validation)
    volume_accuracy = (accurate_counts / total_types) * 100 if total_types > 0 else 0
    
    report.append(f"   ├── Accurate counts: {accurate_counts}/{total_types} ({volume_accuracy:.1f}%)")
    
    # Top volume discrepancies
    volume_discrepancies = sorted(
        [(k, v) for k, v in volume_validation.items() if not v['count_accurate']],
        key=lambda x: abs(x[1]['count_difference']),
        reverse=True
    )[:5]
    
    if volume_discrepancies:
        report.append(f"   └── Top volume discrepancies:")
        for type_name, data in volume_discrepancies:
            diff = data['count_difference']
            sign = "+" if diff > 0 else ""
            report.append(f"       ├── {type_name}: config={data['config_count']}, actual={data['data_count']} ({sign}{diff})")
    
    # Ranking Accuracy
    report.append(f"\n🏆 RANKING ACCURACY ANALYSIS")
    accurate_ranks = sum(1 for v in ranking_analysis.values() if v['rank_accurate'])
    total_ranked = len(ranking_analysis)
    ranking_accuracy = (accurate_ranks / total_ranked) * 100 if total_ranked > 0 else 0
    
    report.append(f"   ├── Accurate rankings: {accurate_ranks}/{total_ranked} ({ranking_accuracy:.1f}%)")
    
    # Top ranking discrepancies
    ranking_discrepancies = sorted(
        [(k, v) for k, v in ranking_analysis.items() if not v['rank_accurate']],
        key=lambda x: abs(x[1]['rank_difference']),
        reverse=True
    )[:5]
    
    if ranking_discrepancies:
        report.append(f"   └── Top ranking discrepancies:")
        for type_name, data in ranking_discrepancies:
            diff = data['rank_difference']
            sign = "+" if diff > 0 else ""
            report.append(f"       ├── {type_name}: config_rank={data['config_rank']}, actual_rank={data['actual_rank']} ({sign}{diff})")
    
    # Calculation Rules Validation
    report.append(f"\n⚙️  CALCULATION RULES VALIDATION")
    for rule_name, rule_data in calculation_validation.items():
        coverage = rule_data['include_coverage']
        report.append(f"   ├── {rule_name}: {coverage:.1f}% type coverage")
        
        if rule_data['missing_include_types']:
            report.append(f"   │   └── Missing types: {', '.join(rule_data['missing_include_types'])}")
    
    # Data Quality Summary
    report.append(f"\n✅ DATA QUALITY SUMMARY")
    total_items = sum(data_volumes.values())
    report.append(f"   ├── Total work items analyzed: {total_items:,}")
    report.append(f"   ├── Type coverage: {coverage_result['coverage_percentage']:.1f}%")
    report.append(f"   ├── Volume accuracy: {volume_accuracy:.1f}%")
    report.append(f"   └── Ranking accuracy: {ranking_accuracy:.1f}%")
    
    overall_score = (coverage_result['coverage_percentage'] + volume_accuracy + ranking_accuracy) / 3
    report.append(f"\n🎯 OVERALL VALIDATION SCORE: {overall_score:.1f}%")
    
    if overall_score >= 90:
        report.append("   Status: ✅ EXCELLENT - Configuration is highly accurate")
    elif overall_score >= 80:
        report.append("   Status: ✅ GOOD - Minor discrepancies detected")
    elif overall_score >= 70:
        report.append("   Status: ⚠️  FAIR - Some adjustments recommended")
    else:
        report.append("   Status: ❌ POOR - Significant updates needed")
    
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    """Main validation function"""
    
    # File paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'work_items.json')
    config_path = os.path.join(base_dir, 'config', 'work_item_types.json')
    
    try:
        # Load data and configuration
        print("Loading work items data...")
        work_items = load_work_items_data(data_path)
        
        print("Loading type mapper configuration...")
        mapper = create_type_mapper(config_path)
        
        # Extract types from data
        print("Analyzing work item types...")
        data_volumes = extract_types_from_data(work_items)
        data_types = set(data_volumes.keys())
        config_types = set(mapper.get_all_types())
        
        # Validate coverage
        print("Validating type coverage...")
        coverage_result = validate_type_coverage(config_types, data_types)
        
        # Validate volumes (extract from config)
        print("Validating volume accuracy...")
        config_volumes = {}
        for type_name in config_types:
            config = mapper.get_type_config(type_name)
            if config:
                config_volumes[type_name] = config.volume['count']
        
        volume_validation = validate_volume_accuracy(config_volumes, data_volumes)
        
        # Validate rankings
        print("Analyzing ranking accuracy...")
        ranking_analysis = analyze_ranking_accuracy(mapper, data_volumes)
        
        # Validate calculation rules
        print("Validating calculation rules...")
        calculation_validation = validate_calculation_rules(mapper, data_types)
        
        # Generate report
        print("Generating validation report...")
        report = generate_validation_report(
            coverage_result,
            volume_validation,
            ranking_analysis,
            calculation_validation,
            data_volumes
        )
        
        # Output report
        print(report)
        
        # Save report to file
        report_path = os.path.join(base_dir, 'WORK_ITEM_TYPES_VALIDATION_REPORT.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Work Item Types Validation Report\n\n")
            f.write(f"Generated: {os.path.basename(__file__)} on {os.path.basename(data_path)}\n\n")
            f.write("```\n")
            f.write(report)
            f.write("\n```\n")
        
        print(f"\n📄 Report saved to: {report_path}")
        
        # Return success/failure based on coverage
        if coverage_result['coverage_percentage'] >= 95:
            print("\n✅ Validation PASSED: Type configuration is accurate")
            return 0
        else:
            print("\n⚠️  Validation WARNINGS: Review discrepancies above")
            return 1
            
    except Exception as e:
        print(f"\n❌ Validation FAILED: {str(e)}")
        return 2


if __name__ == "__main__":
    sys.exit(main())