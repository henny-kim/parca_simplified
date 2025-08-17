#!/usr/bin/env python3
"""
Check Enhanced Extraction Progress
Compare enhanced extraction results with original data
"""

import json
import os
from datetime import datetime

def load_original_data():
    """Load original clinical efficacy data"""
    try:
        with open('clinical_efficacy_azacitidine.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_enhanced_data():
    """Load enhanced clinical efficacy data"""
    try:
        with open('clinical_efficacy_azacitidine_enhanced.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_enhanced_checkpoint():
    """Load enhanced checkpoint data"""
    try:
        with open('clinical_efficacy_azacitidine_enhanced_checkpoint.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def analyze_data_improvements(original_data, enhanced_data):
    """Analyze improvements in data extraction"""
    
    print("📊 DATA EXTRACTION IMPROVEMENT ANALYSIS")
    print("="*60)
    
    # Original data analysis
    original_efficacy = [p for p in original_data if p.get('has_efficacy_data', False)]
    original_pfs = [p for p in original_data if p.get('progression_free_survival_median') is not None]
    original_os = [p for p in original_data if p.get('overall_survival_median') is not None]
    original_cr = [p for p in original_data if p.get('complete_response') is not None]
    original_orr = [p for p in original_data if p.get('overall_response_rate') is not None]
    
    print(f"📋 ORIGINAL DATA:")
    print(f"   • Total papers: {len(original_data)}")
    print(f"   • Papers with efficacy: {len(original_efficacy)}")
    print(f"   • PFS data: {len(original_pfs)} papers")
    print(f"   • OS data: {len(original_os)} papers")
    print(f"   • CR data: {len(original_cr)} papers")
    print(f"   • ORR data: {len(original_orr)} papers")
    
    # Enhanced data analysis
    if enhanced_data:
        enhanced_efficacy = [p for p in enhanced_data if p.get('has_efficacy_data', False)]
        enhanced_pfs = [p for p in enhanced_data if p.get('progression_free_survival_median') is not None]
        enhanced_os = [p for p in enhanced_data if p.get('overall_survival_median') is not None]
        enhanced_cr = [p for p in enhanced_data if p.get('complete_response') is not None]
        enhanced_orr = [p for p in enhanced_data if p.get('overall_response_rate') is not None]
        enhanced_therapy_cycles = [p for p in enhanced_data if p.get('therapy_cycles_median') is not None]
        enhanced_ae = [p for p in enhanced_data if p.get('serious_ae_rate') is not None]
        
        print(f"\n📈 ENHANCED DATA:")
        print(f"   • Total papers: {len(enhanced_data)}")
        print(f"   • Papers with efficacy: {len(enhanced_efficacy)}")
        print(f"   • PFS data: {len(enhanced_pfs)} papers")
        print(f"   • OS data: {len(enhanced_os)} papers")
        print(f"   • CR data: {len(enhanced_cr)} papers")
        print(f"   • ORR data: {len(enhanced_orr)} papers")
        print(f"   • Therapy cycles: {len(enhanced_therapy_cycles)} papers")
        print(f"   • Serious AE: {len(enhanced_ae)} papers")
        
        # Calculate improvements
        pfs_improvement = len(enhanced_pfs) - len(original_pfs)
        os_improvement = len(enhanced_os) - len(original_os)
        cr_improvement = len(enhanced_cr) - len(original_cr)
        orr_improvement = len(enhanced_orr) - len(original_orr)
        
        print(f"\n🚀 IMPROVEMENTS:")
        print(f"   • PFS data: {len(original_pfs)} → {len(enhanced_pfs)} ({pfs_improvement:+d})")
        print(f"   • OS data: {len(original_os)} → {len(enhanced_os)} ({os_improvement:+d})")
        print(f"   • CR data: {len(original_cr)} → {len(enhanced_cr)} ({cr_improvement:+d})")
        print(f"   • ORR data: {len(original_orr)} → {len(enhanced_orr)} ({orr_improvement:+d})")
        print(f"   • NEW: Therapy cycles: {len(enhanced_therapy_cycles)} papers")
        print(f"   • NEW: Serious AE: {len(enhanced_ae)} papers")
    
    # Checkpoint analysis
    checkpoint_data = load_enhanced_checkpoint()
    if checkpoint_data:
        checkpoint_efficacy = [p for p in checkpoint_data if p.get('has_efficacy_data', False)]
        checkpoint_pfs = [p for p in checkpoint_data if p.get('progression_free_survival_median') is not None]
        checkpoint_os = [p for p in checkpoint_data if p.get('overall_survival_median') is not None]
        checkpoint_therapy_cycles = [p for p in checkpoint_data if p.get('therapy_cycles_median') is not None]
        
        print(f"\n⏳ CHECKPOINT STATUS (Enhanced extraction in progress):")
        print(f"   • Papers processed: {len(checkpoint_data)}")
        print(f"   • Papers with efficacy: {len(checkpoint_efficacy)}")
        print(f"   • PFS data found: {len(checkpoint_pfs)} papers")
        print(f"   • OS data found: {len(checkpoint_os)} papers")
        print(f"   • Therapy cycles found: {len(checkpoint_therapy_cycles)} papers")
        
        # Show some examples of new data
        if checkpoint_pfs:
            print(f"\n📝 PFS EXAMPLES FROM ENHANCED EXTRACTION:")
            for i, paper in enumerate(checkpoint_pfs[:3]):
                print(f"   {i+1}. PMID {paper['pmid']}: {paper['progression_free_survival_median']} months")
        
        if checkpoint_therapy_cycles:
            print(f"\n📝 THERAPY CYCLES EXAMPLES FROM ENHANCED EXTRACTION:")
            for i, paper in enumerate(checkpoint_therapy_cycles[:3]):
                print(f"   {i+1}. PMID {paper['pmid']}: {paper['therapy_cycles_median']} cycles")

def main():
    """Main analysis function"""
    print("🔍 Checking enhanced extraction progress...")
    
    # Load data
    original_data = load_original_data()
    enhanced_data = load_enhanced_data()
    
    if not original_data:
        print("❌ No original data found")
        return
    
    # Analyze improvements
    analyze_data_improvements(original_data, enhanced_data)
    
    print(f"\n📅 Analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
