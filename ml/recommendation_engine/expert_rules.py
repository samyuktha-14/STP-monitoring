from typing import Dict, Any, List, Optional, Set


class STPExpertRules:
    """
    Expert rules engine translating multi-sensor symptoms into specific physical equipment actions.
    """

    @staticmethod
    def evaluate_plant_condition(
        readings: Dict[str, float],
        trend_data: Optional[Dict[str, Any]] = None,
        anomaly_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates current readings and trends to generate prioritized action checklists.
        """
        ph = readings.get("pH", 7.1)
        tds = readings.get("TDS", 425.0)
        turbidity = readings.get("Turbidity", 3.5)
        do_val = readings.get("DO", 2.7)
        bod = readings.get("BOD", 13.0)
        cod = readings.get("COD", 53.0)
        tss = readings.get("TSS", 9.4)

        priority_1 = []  # Immediate critical (< 30 mins)
        priority_2 = []  # Process adjustment (< 4 hours)
        priority_3 = []  # Routine preventive check (< 24 hours)
        affected_units = set()

        # =========================================================================
        # 1. AERATION BASIN & BLOWER SYSTEM (DO & pH diagnostics)
        # =========================================================================
        if do_val < 1.5:
            affected_units.add("Aeration Basin (Blowers & Diffusers)")
            priority_1.append({
                "action": "Increase Aeration Blower VFD Speed Immediately",
                "detail": f"Dissolved Oxygen is critically low ({do_val:.2f} mg/L < 1.5 mg/L). Risk of septic conditions, hydrogen sulfide odors, and biomass suffocation.",
                "equipment": "Main Aeration Blowers (VFD 1 & 2)",
                "target": "Raise basin DO to 2.5 - 3.5 mg/L"
            })
            priority_2.append({
                "action": "Inspect Air Diffuser Grid for Fouling / Backpressure",
                "detail": "Check blower pressure gauge for high discharge backpressure indicating fouled coarse/fine bubble diffusers.",
                "equipment": "Submerged Diffuser Air Headers",
                "target": "Ensure uniform air boiling pattern across aeration tank surface"
            })
        elif do_val < 2.0:
            affected_units.add("Aeration Basin (Blowers)")
            priority_2.append({
                "action": "Increase Air Blower Frequency by 5-10%",
                "detail": f"Sub-optimal DO ({do_val:.2f} mg/L). Target is 2.0 - 3.5 mg/L for complete organic oxidation and nitrification.",
                "equipment": "Aeration Blower Control Panel",
                "target": "Target DO 2.5 mg/L"
            })
        elif do_val > 4.5:
            affected_units.add("Aeration Basin (Energy Optimization)")
            priority_2.append({
                "action": "Reduce Aeration Blower Speed to Save Power",
                "detail": f"Effluent is over-aerated ({do_val:.2f} mg/L > 4.5 mg/L). High aeration shears delicate biological floc and wastes electricity.",
                "equipment": "Blower VFD",
                "target": "Lower DO to optimal 2.5 - 3.0 mg/L"
            })

        # =========================================================================
        # 2. SECONDARY CLARIFIER & SLUDGE HANDLING (Turbidity & TSS diagnostics)
        # =========================================================================
        if turbidity > 6.0:
            affected_units.add("Secondary Clarifier & Sludge Recycling")
            priority_1.append({
                "action": "Inspect Clarifier Sludge Blanket & Trigger Sand Filter Backwash",
                "detail": f"Elevated turbidity ({turbidity:.1f} NTU) indicates solid carryover from secondary clarifier settling zone.",
                "equipment": "Secondary Clarifier & Dual Media Sand Filter",
                "target": "Lower turbidity to < 3.0 NTU"
            })
            priority_2.append({
                "action": "Adjust Return Activated Sludge (RAS) Recycle Rate",
                "detail": "Increase RAS pump speed to evacuate settled sludge before it rises and overflows the effluent weir.",
                "equipment": "RAS Pumps 1 & 2",
                "target": "Maintain sludge blanket depth at bottom 1/3 of clarifier"
            })
            priority_3.append({
                "action": "Clean Clarifier V-Notch Effluent Weirs",
                "detail": "Scrape algae and scum buildup from clarifier peripheral overflow launders.",
                "equipment": "Clarifier Launder Weirs",
                "target": "Prevent localized flow channeling"
            })
        elif turbidity > 4.5:
            affected_units.add("Tertiary Sand / Carbon Filter")
            priority_2.append({
                "action": "Perform Scheduled Filter Backwashing",
                "detail": f"Turbidity ({turbidity:.1f} NTU) approaching upper threshold. Initiate backwash cycle with air scouring on Dual Media Filter (DMF).",
                "equipment": "Dual Media Filter (DMF) & Activated Carbon Filter (ACF)",
                "target": "Restore clean filter differential pressure"
            })

        # =========================================================================
        # 3. EQUALIZATION TANK & INLET SALINITY (TDS & pH balance)
        # =========================================================================
        if tds > 600.0:
            affected_units.add("Equalization Tank & Influent Screen")
            priority_2.append({
                "action": "Check Raw Sewage Inlet for Chemical / Softener Brine Dumping",
                "detail": f"TDS elevated ({tds:.0f} mg/L). Investigate domestic water softener regeneration discharges or commercial kitchen grease.",
                "equipment": "Raw Sewage Inlet Chamber & Bar Screens",
                "target": "Ensure adequate mixing in Equalization Basin"
            })

        if ph < 6.5 or ph > 8.5:
            affected_units.add("Chemical Neutralization Dosing System")
            severity_act = priority_1 if (ph < 6.0 or ph > 9.0) else priority_2
            severity_act.append({
                "action": f"Adjust pH Correction Dosing Pump ({'Add Alkali/Lime' if ph < 6.5 else 'Add Acid/Alum'})",
                "detail": f"Effluent pH ({ph:.2f}) violates CPCB discharge compliance (6.5 - 8.5). High/low pH severely inhibits biological bacteria.",
                "equipment": "Chemical Dosing Tank & Metering Pump",
                "target": "Restore neutral pH (7.0 - 7.5)"
            })

        # =========================================================================
        # 4. ROUTINE PREVENTIVE CHECKS (Priority 3)
        # =========================================================================
        priority_3.append({
            "action": "Clean and Recalibrate Live Sensor Probes",
            "detail": "Perform weekly sensor wipe with distilled water and check 2-point calibration buffer for pH and optical lens for turbidity.",
            "equipment": "Physical In-line Sensor Probes (pH, TDS, Turbidity)",
            "target": "Maintain ±2% measurement precision"
        })
        priority_3.append({
            "action": "Log Daily Sludge Volume Index (SVI 30-min Settling Test)",
            "detail": "Take 1-liter aeration basin sample in a graduated cylinder to verify good biological floc settling characteristics (Ideal SVI: 80 - 120 mL/g).",
            "equipment": "On-site Operator Testing Kit",
            "target": "Early biological bulking detection"
        })

        # Overall Plant Operational Status
        if len(priority_1) > 0:
            overall_status = "CRITICAL_INTERVENTION_REQUIRED"
            status_color = "#EF4444"
            headline = f"[CRITICAL] Immediate Plant Action Needed: {priority_1[0]['action']}"
        elif len(priority_2) > 0:
            overall_status = "PROCESS_ADJUSTMENT_RECOMMENDED"
            status_color = "#F59E0B"
            headline = f"[ADVISORY] Process Adjustment: {priority_2[0]['action']}"
        else:
            overall_status = "OPTIMAL_OPERATION"
            status_color = "#10B981"
            headline = "[NORMAL] All Units Operating in Optimal Range. Maintain Standard Routine."

        return {
            "overall_status": overall_status,
            "status_color": status_color,
            "headline_summary": headline,
            "affected_equipment_units": list(affected_units) if len(affected_units) > 0 else ["All Standard Process Units"],
            "action_checklist": {
                "priority_1_immediate": priority_1,
                "priority_2_short_term": priority_2,
                "priority_3_routine_maintenance": priority_3
            }
        }
