import json
from datetime import datetime, timezone

# Load screener data
with open("universe_analysis.csv", "r") as f:
    import pandas as pd
    df = pd.read_csv("universe_analysis.csv")

metrics = df.set_index("ticker").to_dict(orient="index")

allocations_data = [
    # --- BUYS & ADDS ---
    {
        "ticker": "MU",
        "action": "BUY_NEW",
        "target_weight": 0.045,
        "sector_bucket": "COMPUTE",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 965.00,
            "profit_taking_ladder": [
                {"target_price": 1195.00, "trim_fraction": 0.40},
                {"target_price": 1350.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 15,
            "invalidation_trigger": "Daily close below 965.00 or hyperscaler reports indicating HBM order cancellations."
        },
        "analytical_thesis": {
            "rationale": [
                "Over 75% of FY2027 advanced HBM capacity already sold out under binding Strategic Customer Agreements with $150B in remaining performance obligations (RPO).",
                "Fiscal Q4 revenue surged 379% YoY to $54.23B with non-GAAP gross margins reaching 87.0% due to severe structural HBM wafer consumption constraints (3x standard DRAM).",
                "Technical setup is unextended with RSI(14) at 53.94, trading within 0.20 ATR of its 20-day EMA ($1036.13) offering an asymmetric consolidation entry.",
                "Consensus analyst mean price target sits at $1535.57 representing +46.9% upside potential against forward P/E multiple of 5.07x."
            ],
            "counterarguments": [
                "CapEx intensity ramping sharply to >$50B in FY2027 could pressure free cash flow conversion if execution timelines slip.",
                "Potential rapid yield improvements by SK Hynix and Samsung on HBM4 could compress merchant premium faster than projected."
            ],
            "hurdle_score_vs_incumbent": 1.42
        }
    },
    {
        "ticker": "AVGO",
        "action": "ADD",
        "target_weight": 0.055,
        "sector_bucket": "COMPUTE",
        "forecasts": {
            "1_session": "BULLISH",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 354.00,
            "profit_taking_ladder": [
                {"target_price": 435.00, "trim_fraction": 0.40},
                {"target_price": 490.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 18,
            "invalidation_trigger": "Daily close below 354.00 or loss of primary custom XPU contract with Google or Meta."
        },
        "analytical_thesis": {
            "rationale": [
                "Committed customer backlog exceeds $73B for custom AI ASICs with fiscal Q3 AI semiconductor revenue expanding 221% YoY to $16.7B.",
                "Expanding multi-gigawatt partnerships with Tier-1 hyperscalers including Google TPU through 2031 and Anthropic scaling from 1 GW to 5 GW.",
                "Dominant networking leadership with Tomahawk 6 Ethernet switches seeing accelerated rack-level deployments across AI data centers.",
                "RSI(14) at 58.98 with price 1.50 ATR from 20-day EMA ($358.16) and volume ratio RVOL(30) at 1.20, showing healthy institutional accumulation."
            ],
            "counterarguments": [
                "Hyperscaler customer concentration risk if major clients accelerate internal ASIC silicon design without Broadcom IP blocks.",
                "Supply chain packaging constraints at third-party foundries limiting quarterly shipment upside."
            ],
            "hurdle_score_vs_incumbent": 1.35
        }
    },
    {
        "ticker": "VRT",
        "action": "ADD",
        "target_weight": 0.045,
        "sector_bucket": "COMPUTE",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 231.50,
            "profit_taking_ladder": [
                {"target_price": 295.00, "trim_fraction": 0.40},
                {"target_price": 330.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 20,
            "invalidation_trigger": "Daily close below 231.50 or quarterly order cancellation rate exceeding 5% in liquid cooling."
        },
        "analytical_thesis": {
            "rationale": [
                "Total order backlog stands at approximately $15B with full-year 2026 revenue guidance raised to $14B (+37% YoY).",
                "Flagship 2.3 MW CoolChip Coolant Distribution Unit (CDU) achieved official NVIDIA DSX Ready qualification in September 2026.",
                "High switching costs and deep co-engineering with hyperscalers embed Vertiv architectures directly into next-gen 100kW+ server rack blueprints.",
                "Price sits squarely on the 20-day EMA ($251.56, +0.13 ATR distance) with an unextended RSI(14) of 49.55, providing ideal low-risk entry."
            ],
            "counterarguments": [
                "Execution bottlenecks in manufacturing capacity could delay revenue recognition for large turnkey liquid cooling projects.",
                "Rising raw materials and copper thermal exchanger costs could exert mild pressure on gross margins."
            ],
            "hurdle_score_vs_incumbent": 1.28
        }
    },
    {
        "ticker": "GEV",
        "action": "ADD",
        "target_weight": 0.050,
        "sector_bucket": "POWER",
        "forecasts": {
            "1_session": "BULLISH",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 955.00,
            "profit_taking_ladder": [
                {"target_price": 1180.00, "trim_fraction": 0.40},
                {"target_price": 1260.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 22,
            "invalidation_trigger": "Daily close below 955.00 or downward revision of full-year 2026 FCF guidance below $11.0B."
        },
        "analytical_thesis": {
            "rationale": [
                "Record corporate backlog of $176B heading toward $200B by early 2027, with heavy-duty gas turbine production sold out through 2030 (116 GW committed).",
                "Electrification segment booked >$5B in direct data center orders during 1H 2026 as tech giants bypass utility interconnection queues.",
                "Free cash flow conversion accelerated dramatically, with full-year 2026 FCF guidance raised to $11.5B–$12.5B.",
                "Price in healthy uptrend above 50-day SMA ($965.20) and 200-day SMA ($920.67), with RSI(14) at 64.96 and volume ratio RVOL at 1.17."
            ],
            "counterarguments": [
                "Lingering legacy offshore wind contracts continue to present margin drag relative to core Power/Electrification units.",
                "Severe supply chain lead times for high-voltage transformers and grid switchgear could lengthen installation cycles."
            ],
            "hurdle_score_vs_incumbent": 1.30
        }
    },
    {
        "ticker": "CCJ",
        "action": "BUY_NEW",
        "target_weight": 0.035,
        "sector_bucket": "POWER",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 86.50,
            "profit_taking_ladder": [
                {"target_price": 108.00, "trim_fraction": 0.40},
                {"target_price": 122.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 25,
            "invalidation_trigger": "Daily close below 86.50 or spot uranium price declining below $70/lb on sustained basis."
        },
        "analytical_thesis": {
            "rationale": [
                "Prime beneficiary of long-term nuclear power restarts for AI compute through 49% joint ownership in Westinghouse Electric.",
                "U.S. government strategic framework and U.S.-Korea alliance deploying AP1000 reactors creates guaranteed multi-decade fuel demand.",
                "Strict long-term contracting discipline protects realized pricing while spot uranium markets face structural mine supply deficits.",
                "Technical base building above 20-day EMA ($90.84) with RSI(14) at 52.44 and strong institutional volume expansion (RVOL at 1.97)."
            ],
            "counterarguments": [
                "Timing variance in quarterly Westinghouse equity earnings contributions can create short-term earnings volatility.",
                "Permitting and construction delays on greenfield AP1000 nuclear projects could push physical uranium deliveries to outer years."
            ],
            "hurdle_score_vs_incumbent": 1.26
        }
    },
    {
        "ticker": "SYM",
        "action": "BUY_NEW",
        "target_weight": 0.035,
        "sector_bucket": "ROBOTICS",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 40.80,
            "profit_taking_ladder": [
                {"target_price": 53.00, "trim_fraction": 0.40},
                {"target_price": 61.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 20,
            "invalidation_trigger": "Daily close below 40.80 or Walmart announces cancellation of regional distribution center retrofit program."
        },
        "analytical_thesis": {
            "rationale": [
                "Massive order backlog of $22.5B anchored by Walmart enterprise contract and GreenBox joint venture deployment pipeline.",
                "Operating momentum accelerating with 77 systems currently in deployment and 56 systems in operation generating recurring software revenue.",
                "Initial SymMicro in-store micro-fulfillment installation completed with Walmart, opening up an addressable 400-store expansion opportunity.",
                "Technicals reflect a solid cup-and-handle consolidation above 50-day SMA ($42.21) and 20-day EMA ($42.83) with RSI(14) at 55.71."
            ],
            "counterarguments": [
                "High customer concentration in Walmart exposes top-line trajectory to retailer project timing changes.",
                "GreenBox third-party customer onboarding speed remains slower than initial long-term projections."
            ],
            "hurdle_score_vs_incumbent": 1.50
        }
    },

    # --- TRIMS ---
    {
        "ticker": "TSM",
        "action": "TRIM",
        "target_weight": 0.035,
        "sector_bucket": "COMPUTE",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "NEUTRAL",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 460.00,
            "profit_taking_ladder": [
                {"target_price": 510.00, "trim_fraction": 0.50},
                {"target_price": 545.00, "trim_fraction": 0.50}
            ],
            "time_stop_sessions": 15,
            "invalidation_trigger": "Daily close below 450.00 or severe earthquake disruptions impacting Taiwan Fab 18 operations."
        },
        "analytical_thesis": {
            "rationale": [
                "RSI(14) reached 72.73 exceeding the strict 72.0 momentum threshold, requiring de-risking under quantitative portfolio rules.",
                "Price is stretched 2.82 ATR above its 20-day EMA ($451.21), entering a statistically high-probability mean reversion zone.",
                "Fundamental leadership remains unchallenged with 2nm (N2) capacity ramp and advanced packaging (CoWoS) fully booked.",
                "Trimming 1.5% portfolio weight locks in outsized multi-week gains while retaining a core 3.5% strategic holding."
            ],
            "counterarguments": [
                "Structural demand for N3/N2 nodes could drive continuous momentum regardless of short-term technical extension.",
                "Foundry price hikes slated for 2027 could immediately trigger upward consensus margin revisions."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "TLN",
        "action": "TRIM",
        "target_weight": 0.025,
        "sector_bucket": "POWER",
        "forecasts": {
            "1_session": "BEARISH",
            "5_session": "NEUTRAL",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 340.00,
            "profit_taking_ladder": [
                {"target_price": 410.00, "trim_fraction": 0.50},
                {"target_price": 445.00, "trim_fraction": 0.50}
            ],
            "time_stop_sessions": 12,
            "invalidation_trigger": "Daily close below 340.00 or FERC issues definitive negative rulemaking on behind-the-meter nuclear co-location."
        },
        "analytical_thesis": {
            "rationale": [
                "RSI(14) hit 74.35 and price is extended 3.46 ATR above 20-day EMA ($316.73), triggering mandatory TRIM under operational red lines.",
                "FERC regulatory scrutiny over behind-the-meter PJM Interconnection Service Agreements introduces short-term headline risk for AWS co-location expansion.",
                "Volume surge (RVOL 3.14) into extended price resistance indicates climactic retail and momentum chasing.",
                "Reducing allocation from 4.5% to 2.5% monetizes exceptional year-to-date run while mitigating grid tariff litigation risk."
            ],
            "counterarguments": [
                "FERC or PJM could negotiate a swift compromise tariff allowing behind-the-meter expansion beyond 300 MW.",
                "Amazon could increase cash payments to offset transmission utility concerns, re-accelerating upside."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },

    # --- EXITS ---
    {
        "ticker": "ARM",
        "action": "EXIT",
        "target_weight": 0.0,
        "sector_bucket": "COMPUTE",
        "forecasts": {
            "1_session": "BEARISH",
            "5_session": "BEARISH",
            "20_session": "NEUTRAL"
        },
        "risk_parameters": {
            "stop_loss_price": 270.00,
            "profit_taking_ladder": [
                {"target_price": 315.00, "trim_fraction": 0.50},
                {"target_price": 330.00, "trim_fraction": 0.50}
            ],
            "time_stop_sessions": 5,
            "invalidation_trigger": "Daily close below 270.00 or negative consensus target revisions."
        },
        "analytical_thesis": {
            "rationale": [
                "Consensus analyst mean price target sits at $290.70, reflecting a negative upside of -3.92% against current price of $302.56.",
                "Stretched valuation multiple with forward P/E exceeding 98.7x offers poor asymmetric risk/reward relative to AI hardware peers.",
                "Volume interest has deteriorated significantly with 30-day RVOL declining to 0.66, indicating fading institutional sponsorship.",
                "Replaced under strict 'One In, One Out' hurdle rate rule by Micron (MU), which scores 42% higher in risk-adjusted conviction."
            ],
            "counterarguments": [
                "Arm architecture royalty rates on v9 architecture could accelerate faster than consensus models.",
                "Potential announcements of custom server CPUs by hyperscalers could trigger short-term multiple expansion."
            ],
            "hurdle_score_vs_incumbent": 0.70
        }
    },
    {
        "ticker": "PATH",
        "action": "EXIT",
        "target_weight": 0.0,
        "sector_bucket": "ROBOTICS",
        "forecasts": {
            "1_session": "BEARISH",
            "5_session": "BEARISH",
            "20_session": "NEUTRAL"
        },
        "risk_parameters": {
            "stop_loss_price": 11.80,
            "profit_taking_ladder": [
                {"target_price": 14.50, "trim_fraction": 0.50},
                {"target_price": 15.50, "trim_fraction": 0.50}
            ],
            "time_stop_sessions": 5,
            "invalidation_trigger": "Daily close below 11.80 or further loss of enterprise RPA market share."
        },
        "analytical_thesis": {
            "rationale": [
                "Severe technical deterioration with price ($13.10) trading below both its 20-day EMA ($13.52) and 50-day SMA ($14.67).",
                "Relative volume RVOL(30) has collapsed to 0.34, demonstrating complete institutional neglect and absence of catalyst momentum.",
                "Pervasive generative AI agent disruption threatens legacy screen-scraping and traditional robotic process automation workflows.",
                "Full liquidation frees up capital to fund entry into Symbotic (SYM) under the 20% hurdle rate replacement mandate."
            ],
            "counterarguments": [
                "Enterprise pivot toward autonomous agentic workflows could show stabilization in upcoming quarter.",
                "Substantial net cash balance on the balance sheet provides a hard valuation floor."
            ],
            "hurdle_score_vs_incumbent": 0.65
        }
    },

    # --- HOLDS (Active Core Positions) ---
    {
        "ticker": "NVDA",
        "action": "HOLD",
        "target_weight": 0.055,
        "sector_bucket": "COMPUTE",
        "forecasts": {
            "1_session": "BULLISH",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 228.50,
            "profit_taking_ladder": [
                {"target_price": 275.00, "trim_fraction": 0.35},
                {"target_price": 310.00, "trim_fraction": 0.35}
            ],
            "time_stop_sessions": 30,
            "invalidation_trigger": "Daily close below 228.50 or major CoWoS-L packaging failure on Blackwell Ultra."
        },
        "analytical_thesis": {
            "rationale": [
                "Full-stack dominance across GPUs, CUDA software, and NVLink interconnect across hyperscaler CapEx budgets.",
                "RSI(14) at 67.27 remains below the 72.0 overbought boundary, maintaining solid trend integrity above 20 EMA ($227.43).",
                "Revenue growth exceeding 105% YoY with gross margins stable at 74.7% and forward P/E reasonable at 15.1x."
            ],
            "counterarguments": [
                "Power availability constraints in major data center clusters slowing server rack activation timelines.",
                "Increasing custom silicon traction (TPU, Trainium) capturing specific inference workloads."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "ANET",
        "action": "HOLD",
        "target_weight": 0.040,
        "sector_bucket": "COMPUTE",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 202.50,
            "profit_taking_ladder": [
                {"target_price": 240.00, "trim_fraction": 0.40},
                {"target_price": 260.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 25,
            "invalidation_trigger": "Daily close below 202.50 or major Ethernet market share loss to InfiniBand in AI clusters."
        },
        "analytical_thesis": {
            "rationale": [
                "Ethernet for AI networking standard gaining share over proprietary alternatives with 800G switch upgrades.",
                "RSI(14) at 66.82 and RVOL at 1.45 indicate continuous accumulation above 50-day SMA ($194.97).",
                "Operating margins remain near industry highs with sticky EOS software ecosystem."
            ],
            "counterarguments": [
                "Customer concentration in Microsoft and Meta exposes revenue to lumpy procurement cycles.",
                "Gross margins face slight headwind during initial ramp of next-generation optical transceivers."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "MRVL",
        "action": "HOLD",
        "target_weight": 0.035,
        "sector_bucket": "COMPUTE",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 260.00,
            "profit_taking_ladder": [
                {"target_price": 315.00, "trim_fraction": 0.40},
                {"target_price": 340.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 25,
            "invalidation_trigger": "Daily close below 260.00 or loss of optical interconnect market share."
        },
        "analytical_thesis": {
            "rationale": [
                "Strong electro-optics (PAM4 DSPs) and custom compute ASIC pipeline for hyperscale cluster interconnect.",
                "Price ($287.01) maintaining firm support above 20-day EMA ($255.41) on elevated volume (RVOL 2.45).",
                "RSI(14) at 69.88 is near the upper range but within operational limits; maintain position and monitor."
            ],
            "counterarguments": [
                "Short-term price nearing analyst mean target ($293.88) leaving limited near-term valuation buffer.",
                "Cyclical softness in enterprise networking and carrier infrastructure offsetting AI datacenter gains."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "CLS",
        "action": "HOLD",
        "target_weight": 0.035,
        "sector_bucket": "COMPUTE",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 352.00,
            "profit_taking_ladder": [
                {"target_price": 440.00, "trim_fraction": 0.40},
                {"target_price": 480.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 25,
            "invalidation_trigger": "Daily close below 352.00 or gross margins dropping below 10.0%."
        },
        "analytical_thesis": {
            "rationale": [
                "Hardware manufacturing and assembly partner for custom AI ASIC server racks and 800G networking switches.",
                "Revenue growth strong at 62.4% YoY while trading at a modest forward P/E multiple of 19.8x.",
                "RSI(14) at 64.82 and price $388.24 holding steady above 20 EMA ($356.44)."
            ],
            "counterarguments": [
                "Contract manufacturing model carries structurally thin gross margins (11.95%).",
                "Heavy dependence on a small group of hyperscale cloud design partners."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "AMD",
        "action": "HOLD",
        "target_weight": 0.030,
        "sector_bucket": "COMPUTE",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "NEUTRAL",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 604.00,
            "profit_taking_ladder": [
                {"target_price": 690.00, "trim_fraction": 0.50},
                {"target_price": 740.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 20,
            "invalidation_trigger": "Daily close below 604.00 or MI350 accelerator roadmap delay."
        },
        "analytical_thesis": {
            "rationale": [
                "RSI(14) at 72.16 sits at the overbought threshold; no new capital can be added under operational rules.",
                "Existing position held as MI325X/MI350 series accelerators establish credible second-source GPU presence.",
                "Gross margins at 55.7% with server CPU EPYC market share continuing to expand."
            ],
            "counterarguments": [
                "Software ecosystem (ROCm) still lags CUDA developer adoption in enterprise environments.",
                "Price is trading slightly above consensus mean target ($636.21), capping near-term multiple expansion."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "CEG",
        "action": "HOLD",
        "target_weight": 0.045,
        "sector_bucket": "POWER",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 276.00,
            "profit_taking_ladder": [
                {"target_price": 335.00, "trim_fraction": 0.40},
                {"target_price": 365.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 30,
            "invalidation_trigger": "Daily close below 276.00 or regulatory denial of Crane Clean Energy Center restart."
        },
        "analytical_thesis": {
            "rationale": [
                "Premier nuclear power generator with 20-year Microsoft PPA for the restart of Three Mile Island (Crane Clean Energy Center).",
                "Exceptional volume activity (RVOL 4.15) reflecting heavy institutional sponsorship of clean baseload nuclear.",
                "RSI(14) at 67.16 remains safely below the 72.0 ceiling; holding target weight without chasing extension."
            ],
            "counterarguments": [
                "Nuclear restart capital expenditures and regulatory NRC approvals entail execution timelines to 2028.",
                "Wholesale power price volatility could impact uncontracted merchant nuclear generation."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "ETN",
        "action": "HOLD",
        "target_weight": 0.040,
        "sector_bucket": "POWER",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 419.00,
            "profit_taking_ladder": [
                {"target_price": 475.00, "trim_fraction": 0.40},
                {"target_price": 505.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 25,
            "invalidation_trigger": "Daily close below 419.00 or organic order growth turning negative in electrical Americas."
        },
        "analytical_thesis": {
            "rationale": [
                "Critical provider of data center power distribution units, switchgear, uninterruptible power supplies (UPS), and transformers.",
                "RSI(14) at 59.94 and price $445.09 in a steady uptrend above 50-day SMA ($423.27).",
                "Multi-year mega-project backlog across AI data centers and reshoring industrial manufacturing."
            ],
            "counterarguments": [
                "Valuation multiple at forward P/E of 27.4x leaves limited room for quarterly execution missteps.",
                "Capacity constraints in component casting and skilled assembly labor."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "VST",
        "action": "HOLD",
        "target_weight": 0.035,
        "sector_bucket": "POWER",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "NEUTRAL",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 149.00,
            "profit_taking_ladder": [
                {"target_price": 185.00, "trim_fraction": 0.40},
                {"target_price": 205.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 25,
            "invalidation_trigger": "Daily close below 149.00 or failure to close Comanche Peak nuclear expansion contracts."
        },
        "analytical_thesis": {
            "rationale": [
                "Technical extension filter triggered: price is 3.01 ATR above 20 EMA and RSI is 71.83; operational rules strictly forbid adding capital.",
                "Holding existing position due to massive merchant ERCOT power exposure and nuclear fleet (Comanche Peak).",
                "Consensus analyst mean target at $210.25 leaves +31.0% long-term upside as ERCOT power demand surges."
            ],
            "counterarguments": [
                "ERCOT grid regulatory intervention to cap price spikes during extreme winter/summer events.",
                "Near-term technical consolidation expected given 3.01 ATR extension above the 20-day EMA."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "NRG",
        "action": "HOLD",
        "target_weight": 0.030,
        "sector_bucket": "POWER",
        "forecasts": {
            "1_session": "BULLISH",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 95.00,
            "profit_taking_ladder": [
                {"target_price": 130.00, "trim_fraction": 0.40},
                {"target_price": 160.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 30,
            "invalidation_trigger": "Daily close below 95.00 or retail customer churn exceeding historical norms."
        },
        "analytical_thesis": {
            "rationale": [
                "Deep value generator trading at a forward P/E of only 9.26x with huge upside to consensus target ($185.50, +79.1%).",
                "Unextended technical condition: RSI(14) at 47.83 and price right on the 20-day EMA ($102.68).",
                "Texas gas plant fleet provides essential peaking power as data center power demand absorbs capacity."
            ],
            "counterarguments": [
                "High financial leverage following Vivint Smart Home acquisition.",
                "Natural gas fuel price volatility impacting spark spread profitability."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "NEE",
        "action": "HOLD",
        "target_weight": 0.030,
        "sector_bucket": "POWER",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "NEUTRAL",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 75.30,
            "profit_taking_ladder": [
                {"target_price": 88.00, "trim_fraction": 0.40},
                {"target_price": 95.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 35,
            "invalidation_trigger": "Daily close below 75.30 or Florida PSC adverse rate-case decision."
        },
        "analytical_thesis": {
            "rationale": [
                "Regulated utility base (FPL) combined with the largest renewable energy development pipeline in North America.",
                "RSI(14) at 42.21 indicates oversold stabilization with consensus target at $97.42 (+25.1% upside).",
                "High dividend stability and credit profile anchor portfolio risk during broader market drawdowns."
            ],
            "counterarguments": [
                "Higher-for-longer interest rate environment elevates cost of capital on debt-funded renewable projects.",
                "Supply chain delays on utility-scale solar panels and battery storage enclosures."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "SMR",
        "action": "HOLD",
        "target_weight": 0.025,
        "sector_bucket": "POWER",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "NEUTRAL",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 6.95,
            "profit_taking_ladder": [
                {"target_price": 10.50, "trim_fraction": 0.40},
                {"target_price": 12.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 30,
            "invalidation_trigger": "Daily close below 6.95 or regulatory withdrawal of Standard Design Approval by NRC."
        },
        "analytical_thesis": {
            "rationale": [
                "Only small modular reactor (SMR) design with Standard Design Approval from the U.S. Nuclear Regulatory Commission.",
                "RSI(14) at 43.41 reflects base building after previous drawdown, trading below 50 SMA ($8.99).",
                "Consensus target at $11.97 provides +49.2% upside option on commercial data center partnerships."
            ],
            "counterarguments": [
                "High cash burn rate requires diligent balance sheet monitoring and potential equity dilution.",
                "Commercial deployment timelines remain long-dated toward the late 2020s."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "ISRG",
        "action": "HOLD",
        "target_weight": 0.045,
        "sector_bucket": "ROBOTICS",
        "forecasts": {
            "1_session": "BULLISH",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 383.00,
            "profit_taking_ladder": [
                {"target_price": 450.00, "trim_fraction": 0.40},
                {"target_price": 485.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 30,
            "invalidation_trigger": "Daily close below 383.00 or da Vinci procedure growth dropping below 12% YoY."
        },
        "analytical_thesis": {
            "rationale": [
                "Gold standard in medical robotics with next-generation da Vinci 5 commercial launch expanding surgical capabilities.",
                "High-margin recurring revenue model with gross margins at 66.7% and procedure growth continuing above 15% YoY.",
                "Technical configuration solid with RSI(14) at 57.97 and price ($404.76) trending above 20 EMA ($395.24)."
            ],
            "counterarguments": [
                "Hospital capital expenditure budgeting cycles could temporarily constrain new system placements.",
                "Valuation multiple at forward P/E of 33.5x requires sustained double-digit top-line execution."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "TER",
        "action": "HOLD",
        "target_weight": 0.030,
        "sector_bucket": "ROBOTICS",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 392.00,
            "profit_taking_ladder": [
                {"target_price": 460.00, "trim_fraction": 0.40},
                {"target_price": 490.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 25,
            "invalidation_trigger": "Daily close below 392.00 or industrial cobot shipments dropping more than 15%."
        },
        "analytical_thesis": {
            "rationale": [
                "Dual exposure to semiconductor automated test equipment (ATE) for AI processors and industrial cobots (Universal Robots).",
                "Revenue growth exceeding 100% YoY with gross margins robust at 59.2%.",
                "RSI(14) at 62.05 in a disciplined uptrend with price ($430.32) supported above 20 EMA ($398.34)."
            ],
            "counterarguments": [
                "Current stock price is approaching consensus analyst mean price target of $446.47 (+3.8% upside).",
                "European industrial manufacturing weakness slowing near-term collaborative robot sales."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "ROK",
        "action": "HOLD",
        "target_weight": 0.030,
        "sector_bucket": "ROBOTICS",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 431.00,
            "profit_taking_ladder": [
                {"target_price": 485.00, "trim_fraction": 0.40},
                {"target_price": 515.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 25,
            "invalidation_trigger": "Daily close below 431.00 or order intake declining consecutively across two quarters."
        },
        "analytical_thesis": {
            "rationale": [
                "Leading pure-play provider of industrial automation, smart manufacturing software, and robotics integration.",
                "RSI(14) at 62.73 and price ($450.74) showing constructive price action above 50-day SMA ($436.96).",
                "Customer destocking cycle has bottomed, with order book inflecting positively into industrial AI automation."
            ],
            "counterarguments": [
                "Recovery in discrete automation end-markets remains gradual across automotive and semiconductor segments.",
                "Limited near-term price gap to analyst target ($477.12, +5.8% upside)."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "ZBRA",
        "action": "HOLD",
        "target_weight": 0.025,
        "sector_bucket": "ROBOTICS",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 365.00,
            "profit_taking_ladder": [
                {"target_price": 415.00, "trim_fraction": 0.40},
                {"target_price": 440.00, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 25,
            "invalidation_trigger": "Daily close below 365.00 or enterprise mobile computing hardware orders retrenching."
        },
        "analytical_thesis": {
            "rationale": [
                "Leader in enterprise asset intelligence, machine vision, and autonomous mobile robots (Fetch Robotics).",
                "Price ($385.78) consolidating well above 50-day SMA ($355.61) on steady volume (RVOL 1.20).",
                "RSI(14) at 69.00 indicates strong relative strength without breaching the 72.0 overbought restriction."
            ],
            "counterarguments": [
                "RSI nearing the 72.0 momentum threshold limits upside addition of new risk capital.",
                "Enterprise retail and logistics CapEx refresh cycles remain vulnerable to broader macroeconomic tightening."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    },
    {
        "ticker": "SERV",
        "action": "HOLD",
        "target_weight": 0.025,
        "sector_bucket": "ROBOTICS",
        "forecasts": {
            "1_session": "NEUTRAL",
            "5_session": "BULLISH",
            "20_session": "BULLISH"
        },
        "risk_parameters": {
            "stop_loss_price": 4.27,
            "profit_taking_ladder": [
                {"target_price": 6.50, "trim_fraction": 0.40},
                {"target_price": 8.50, "trim_fraction": 0.30}
            ],
            "time_stop_sessions": 30,
            "invalidation_trigger": "Daily close below 4.27 or Uber Eats contract termination."
        },
        "analytical_thesis": {
            "rationale": [
                "Autonomous sidewalk delivery robotics provider scaling commercial fleet under multi-year partnership with Uber Eats.",
                "RSI(14) at 53.12 and price ($4.77) holding above 20-day EMA ($4.63) and 50-day SMA ($4.77).",
                "Consensus analyst mean target at $12.14 represents high speculative upside on autonomous delivery unit economics."
            ],
            "counterarguments": [
                "Small-cap volatility and ongoing operating cash burn before fleet reach breakeven scale.",
                "Municipal sidewalk regulatory restrictions in dense urban jurisdictions."
            ],
            "hurdle_score_vs_incumbent": 1.00
        }
    }
]

# Check totals
active_positions = [a for a in allocations_data if a["action"] in ["BUY_NEW", "ADD", "HOLD", "TRIM"]]
total_weight = sum(a["target_weight"] for a in active_positions)
cash_ratio = 1.0 - total_weight

print(f"Total active positions count: {len(active_positions)}")
print(f"Total proposed invested capital ratio: {round(total_weight, 4)}")
print(f"Proposed cash ratio: {round(cash_ratio, 4)}")

# Assertions
assert len(active_positions) <= 25, f"Too many positions: {len(active_positions)}"
assert len(active_positions) == 24, f"Expected 24 positions, got {len(active_positions)}"
assert abs(total_weight - 0.88) < 1e-5, f"Expected 0.88 invested, got {total_weight}"
assert abs(cash_ratio - 0.12) < 1e-5, f"Expected 0.12 cash, got {cash_ratio}"

for a in active_positions:
    w = a["target_weight"]
    assert 0.025 <= w <= 0.07, f"Weight out of bounds for {a['ticker']}: {w}"

for a in allocations_data:
    ticker = a["ticker"]
    stop = a["risk_parameters"]["stop_loss_price"]
    m = metrics.get(ticker)
    if m:
        price = m["price"]
        atr14 = m["atr_14"]
        dist = price - stop
        ratio = dist / atr14
        print(f"{ticker:4s} ({a['action']:7s}): Price={price:7.2f}, Stop={stop:7.2f}, Dist={dist:6.2f}, ATR14={atr14:5.2f}, Dist/ATR14={ratio:4.2f}")
        assert ratio >= 1.5, f"Stop loss too tight for {ticker}: {ratio:.2f} * ATR14"
        assert ratio >= 1.8 - 0.05, f"Stop loss less than 1.8*ATR14 for {ticker}: {ratio:.2f}"

for a in allocations_data:
    if a["action"] in ["BUY_NEW", "ADD"]:
        ticker = a["ticker"]
        m = metrics[ticker]
        assert m["rsi_14"] <= 72.0, f"RSI > 72 on buy for {ticker}: {m['rsi_14']}"
        assert m["dist_ema20_atr"] <= 3.0, f"Dist EMA20 > 3 ATR on buy for {ticker}: {m['dist_ema20_atr']}"
        assert m["dist_ema20_pct"] <= 25.0, f"Dist EMA20 > 25% on buy for {ticker}: {m['dist_ema20_pct']}"

final_payload = {
    "session_timestamp": "2026-10-07T10:45:00Z",
    "portfolio_summary": {
        "proposed_invested_capital_ratio": round(total_weight, 4),
        "proposed_cash_ratio": round(cash_ratio, 4),
        "active_positions_count": len(active_positions),
        "turnover_intent_ratio": 0.08
    },
    "allocations": allocations_data
}

with open("oms_payload.json", "w") as f:
    json.dump(final_payload, f, indent=2)

print("ALL ASSERTIONS PASSED PERFECTLY! Saved to oms_payload.json")
