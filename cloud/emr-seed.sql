-- EMR (electronic medical record) - Riverbend Home Medical Clinic (fictional)  -- schema v7
--
-- v7: staff register (seat -> role). A seat is a NAME, not an authenticated user
-- (deliberate demo scope). All power comes from registers: clinicians (who may
-- sign and record bedside services), staff role 'director' (who rules on flags
-- and confirms claims). Sim-Director is added to BOTH registers only while
-- judging runs (pilot-on.sh) and removed after - disclosed in /how.
-- NOTE: Entirely synthetic. No real patient, clinician, practice or visit exists here.
--
-- v6: fictional billing (Nagisa Schedule). fee_schedule master / visit_services
-- (entered before signing, frozen by it) / charges (derived by the pulse from
-- SIGNED visits only; over-cap lines are 0-point FLAGS for a human ruling) /
-- claims (one per patient-month; confirmed claims and their charges are locked
-- by a trigger). July is imported pre-Troupe as confirmed legacy. Every code,
-- point value and payer is INVENTED - the structure mirrors reality, the
-- numbers do not.
--
-- v5: clinicians master (FK from patterns/visits/notes) / signing closes the loop
-- (signed note INSERT + visit done + draft used, one transaction; enforced by
-- UNIQUE(visit_id), a status guard, and an immutability trigger) /
-- visit_patterns.interval_weeks (biweekly) / visits.cancelled_reason.
--
-- Master data (slow-changing) and clinical data (event streams) are kept apart.
-- clinical_notes holds SIGNED (final) notes only - append-only, never edited.
-- note_drafts is the draft inbox: Troupe deposits approved drafts here, a doctor
-- rewrites and signs elsewhere. Troupe has no path that writes a signed note.

DROP TABLE IF EXISTS staff, charges, claims, visit_services, fee_schedule,
  note_drafts, clinical_notes, condition_events,
  visits, visit_patterns, physician_orders, medications, patient_conditions,
  patients, clinicians, clinic CASCADE;
DROP FUNCTION IF EXISTS clinical_notes_immutable() CASCADE;
DROP FUNCTION IF EXISTS billing_locked() CASCADE;
DROP FUNCTION IF EXISTS charges_no_insert_into_confirmed() CASCADE;
DROP FUNCTION IF EXISTS services_frozen_by_signing() CASCADE;

-- ========== master ==========

CREATE TABLE clinic(               -- the practice's home base (route origin)
  name TEXT NOT NULL,
  lat DOUBLE PRECISION NOT NULL,
  lng DOUBLE PRECISION NOT NULL
);

CREATE TABLE staff(                  -- the register of CLERICAL seats: name -> role.
  name TEXT PRIMARY KEY,             -- clinical power is gated by clinicians(active) alone;
  role TEXT NOT NULL CHECK (role IN ('director','clerk'))   -- the seat picker unions both.
);

CREATE TABLE clinicians(
  code TEXT PRIMARY KEY,            -- 'Dr-A' : the free strings survive unchanged as keys
  active BOOLEAN NOT NULL DEFAULT true   -- display is always the code
);

CREATE TABLE patients(
  code TEXT PRIMARY KEY,
  age INTEGER NOT NULL,
  living_situation TEXT NOT NULL,
  -- "home" address: a PUBLIC landmark standing in for a residence, so the demo
  -- has real geography while pointing at nobody's actual home.
  address TEXT NOT NULL,
  lat DOUBLE PRECISION NOT NULL,
  lng DOUBLE PRECISION NOT NULL,
  -- billing (all fictional): copay 10/20/30%, same-building grouping, severe flag
  copay_rate INTEGER NOT NULL DEFAULT 3 CHECK (copay_rate IN (1,2,3)),
  building TEXT,                       -- null = own home; shared id = same building
  severe BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE patient_conditions(
  patient TEXT NOT NULL REFERENCES patients(code),
  dx TEXT NOT NULL,
  is_primary BOOLEAN NOT NULL DEFAULT false,
  onset DATE
);

CREATE TABLE medications(
  patient TEXT NOT NULL REFERENCES patients(code),
  drug TEXT NOT NULL,
  dose TEXT NOT NULL,
  frequency TEXT NOT NULL,
  started DATE NOT NULL,
  stopped DATE            -- null = current
);

-- ========== clinical ==========

CREATE TABLE physician_orders(
  patient TEXT NOT NULL REFERENCES patients(code),
  practice TEXT NOT NULL,
  signed DATE NOT NULL,
  expires DATE NOT NULL,
  order_type TEXT NOT NULL
);

-- Three layers, kept apart:
--   visit_patterns  = the recurring plan  (who visits whom, which weekday)   - master
--   visits          = generated instances (one row per planned visit)        - schedule
--   clinical_notes  = the signed record, linked to the visit it documents    - record
-- Deciding a pattern is the human judgment; EXPANDING it into instances is
-- bookkeeping, and Troupe's pulse does it (plan_visits, idempotent on
-- (pattern_id, visit_date)). Weekly Visit Prep still flags patterns with no
-- scheduled instance - the safety net for silent write failures.

CREATE TABLE visit_patterns(
  id BIGSERIAL PRIMARY KEY,
  patient TEXT NOT NULL REFERENCES patients(code),
  weekday INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),  -- 0=Sun .. 6=Sat
  clinician TEXT NOT NULL REFERENCES clinicians(code),
  purpose TEXT NOT NULL,
  interval_weeks INTEGER NOT NULL DEFAULT 1 CHECK (interval_weeks BETWEEN 1 AND 12),
  active_from DATE NOT NULL,
  active_to DATE                                              -- null = open-ended
);

CREATE TABLE visits(
  id BIGSERIAL PRIMARY KEY,
  pattern_id BIGINT REFERENCES visit_patterns(id),            -- null = ad-hoc visit
  visit_date DATE NOT NULL,
  patient TEXT NOT NULL REFERENCES patients(code),
  clinician TEXT NOT NULL REFERENCES clinicians(code),
  purpose TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'scheduled'
    CHECK (status IN ('scheduled','done','cancelled')),
  cancelled_reason TEXT,
  -- regular = planned care (visit fee, weekly cap applies) / urgent = on-call
  kind TEXT NOT NULL DEFAULT 'regular' CHECK (kind IN ('regular','urgent')),
  UNIQUE (pattern_id, visit_date)                             -- 取り決め×日付は一度だけ
);

CREATE TABLE clinical_notes(          -- SIGNED notes only. Append-only. Immutable.
  id BIGSERIAL PRIMARY KEY,
  patient TEXT NOT NULL REFERENCES patients(code),
  visit_id BIGINT REFERENCES visits(id) UNIQUE,               -- one signed note per visit
  note_date DATE NOT NULL,
  clinician TEXT NOT NULL REFERENCES clinicians(code),
  s TEXT NOT NULL, o TEXT NOT NULL, a TEXT NOT NULL, p TEXT NOT NULL,
  signed_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE note_drafts(             -- the draft inbox. Append-only: the deposit INSERT
  id BIGSERIAL PRIMARY KEY,           -- is the ONLY writer; signing never touches this table.
  patient TEXT NOT NULL REFERENCES patients(code),
  visit_date DATE NOT NULL,           -- which visit this draft is addressed to
  body TEXT NOT NULL,
  based_on_job TEXT NOT NULL UNIQUE,  -- idempotency: one deposit per approved job
  delivered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (patient, visit_date)        -- one draft per visit; 'used' is derived from the signed note
);

-- the natural key: one live regular visit per patient per day — this is what
-- lets drafts (and the Origin key) address a visit as (patient, visit_date)
CREATE UNIQUE INDEX visits_one_regular_per_day ON visits(patient, visit_date)
  WHERE kind = 'regular' AND status <> 'cancelled';
CREATE INDEX idx_visits_day ON visits(visit_date, status);
CREATE INDEX idx_visits_patient ON visits(patient, visit_date DESC);
CREATE INDEX idx_notes_patient ON clinical_notes(patient, note_date DESC);

-- ========== billing (Nagisa Schedule - entirely fictional) ==========

CREATE TABLE fee_schedule(
  code TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('visit','oncall','act','drug','material','addon','monthly')),
  points INTEGER,                      -- direct points (visit/oncall/act/addon/monthly)
  price_yen NUMERIC(10,2),             -- drugs & materials are priced in yen, converted at derivation
  unit TEXT NOT NULL CHECK (unit IN ('per_event','per_day','per_week','per_month','per_quarter')),
  weekly_cap INTEGER,
  note TEXT NOT NULL DEFAULT '',
  CHECK ((points IS NULL) <> (price_yen IS NULL))
);

CREATE TABLE visit_services(            -- what was done at the bedside. Human-entered, frozen by signing.
  id BIGSERIAL PRIMARY KEY,
  visit_id BIGINT NOT NULL REFERENCES visits(id),
  code TEXT NOT NULL REFERENCES fee_schedule(code),
  qty INTEGER NOT NULL CHECK (qty >= 1),
  recorded_by TEXT NOT NULL,
  UNIQUE (visit_id, code)
);

CREATE TABLE claims(                    -- one per patient-month. confirmed = fact, locked.
  id BIGSERIAL PRIMARY KEY,
  patient TEXT NOT NULL REFERENCES patients(code),
  month TEXT NOT NULL,                  -- 'YYYY-MM'
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','confirmed')),
  total_points INTEGER NOT NULL DEFAULT 0,
  copay_rate INTEGER NOT NULL,
  copay_yen INTEGER NOT NULL DEFAULT 0,
  confirmed_by TEXT,
  confirmed_at TIMESTAMPTZ,
  CHECK ((status = 'confirmed') = (confirmed_by IS NOT NULL)),
  UNIQUE (patient, month)
);

CREATE TABLE charges(                   -- derived lines. flagged = 0 points, waiting for a human ruling.
  id BIGSERIAL PRIMARY KEY,
  patient TEXT NOT NULL REFERENCES patients(code),
  month TEXT NOT NULL,
  day DATE NOT NULL,
  visit_id BIGINT REFERENCES visits(id),
  code TEXT NOT NULL REFERENCES fee_schedule(code),
  qty INTEGER NOT NULL DEFAULT 1,
  points INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'derived'
    CHECK (status IN ('derived','flagged','allowed','dropped')),
  flag_reason TEXT,
  resolve_reason TEXT,
  resolved_by TEXT,
  UNIQUE (visit_id, code)               -- derivation is idempotent per visit x item
);
CREATE UNIQUE INDEX idx_charges_monthly ON charges(patient, month, code)
  WHERE visit_id IS NULL AND code LIKE 'NC%';
CREATE INDEX idx_charges_month ON charges(month, patient);

CREATE TABLE condition_events(
  patient TEXT NOT NULL REFERENCES patients(code),
  event_date DATE NOT NULL,
  description TEXT NOT NULL
);

-- ========== seed: master ==========

INSERT INTO clinicians(code) VALUES ('Dr-A'), ('Dr-B'), ('Dr-C');

INSERT INTO staff(name, role) VALUES
 ('Director', 'director');

INSERT INTO clinic VALUES
 ('Riverbend Home Medical Clinic', 35.6433, 139.6690);

INSERT INTO patients VALUES
 ('P-001', 82, 'lives alone, daughter visits weekends', 'Setagaya City Hall (public landmark stand-in)', 35.6432, 139.6532, 1, NULL, false),
 ('P-002', 74, 'lives with spouse', 'Komazawa Olympic Park (public landmark stand-in)', 35.6265, 139.6620, 2, NULL, false),
 ('P-003', 76, 'lives with spouse', 'Shoin Shrine (public landmark stand-in)', 35.6444, 139.6567, 1, NULL, false),
 ('P-004', 88, 'Nagisa Court (fictional care facility), room 101', 'Gotokuji Temple (public landmark stand-in)', 35.6488, 139.6470, 1, 'nagisa-court', false),
 ('P-005', 68, 'lives with son''s family', 'Setagaya Park (public landmark stand-in)', 35.6398, 139.6720, 3, NULL, false),
 ('P-006', 79, 'lives alone, neighbour checks in', 'Shimokitazawa Sta. (public landmark stand-in)', 35.6613, 139.6667, 1, NULL, false),
 ('P-007', 84, 'lives with spouse', 'Meidaimae Sta. (public landmark stand-in)', 35.6685, 139.6371, 1, NULL, false),
 ('P-008', 71, 'lives alone', 'Futako-Tamagawa Sta. (public landmark stand-in)', 35.6117, 139.6265, 2, NULL, false),
 ('P-009', 90, 'Nagisa Court (fictional care facility), room 203', 'Gotokuji Temple (public landmark stand-in)', 35.6488, 139.6470, 1, 'nagisa-court', false),
 ('P-010', 66, 'lives with spouse', 'Soshigaya-Okura Sta. (public landmark stand-in)', 35.6417, 139.6089, 3, NULL, true);

INSERT INTO patient_conditions VALUES
 ('P-001','congestive heart failure, NYHA II', true,  '2023-11-01'),
 ('P-001','hypertension',                      false, '2015-03-01'),
 ('P-002','type 2 diabetes',                   true,  '2012-06-01'),
 ('P-002','peripheral neuropathy',             false, '2021-02-01'),
 ('P-003','Parkinson''s disease, Hoehn-Yahr 3',true,  '2018-09-01'),
 ('P-004','stroke sequelae, right hemiparesis',true,  '2024-12-15'),
 ('P-005','COPD GOLD III',                     true,  '2019-04-01'),
 ('P-006','chronic kidney disease stage 4',    true,  '2020-08-01'),
 ('P-007','atrial fibrillation',               true,  '2022-01-10'),
 ('P-008','post hip replacement',              true,  '2026-06-30'),
 ('P-009','advanced dementia',                 true,  '2021-05-01'),
 ('P-010','metastatic colon cancer',           true,  '2026-05-20');

INSERT INTO medications(patient, drug, dose, frequency, started, stopped) VALUES
 ('P-001','furosemide','20mg','qd','2023-11-10',NULL),
 ('P-001','furosemide','40mg','qd','2023-11-01','2023-11-10'),   -- lowered after response
 ('P-001','lisinopril','10mg','qd','2015-03-01',NULL),
 ('P-001','aspirin','81mg','qd','2015-03-01',NULL),
 ('P-002','metformin','500mg','bid','2012-06-01',NULL),
 ('P-002','insulin glargine','12u','qhs','2020-01-15',NULL),
 ('P-002','gabapentin','300mg','tid','2021-02-01',NULL),
 ('P-003','levodopa/carbidopa','100/25','tid','2018-09-01',NULL),
 ('P-003','rasagiline','1mg','qd','2019-06-01',NULL),
 ('P-004','clopidogrel','75mg','qd','2024-12-20',NULL),
 ('P-004','atorvastatin','40mg','qd','2024-12-20',NULL),
 ('P-005','tiotropium','18mcg','qd','2019-04-01',NULL),
 ('P-005','salmeterol-fluticasone','50/500','bid','2022-10-01',NULL),
 ('P-005','prednisone taper','per schedule','ends 2026-08-25','2026-08-08',NULL),
 ('P-006','sevelamer','800mg','tid with meals','2021-01-01',NULL),
 ('P-006','darbepoetin','40mcg','weekly','2023-03-01',NULL),
 ('P-007','apixaban','5mg','bid','2022-01-10',NULL),
 ('P-007','metoprolol','50mg','bid','2026-08-12',NULL),
 ('P-007','metoprolol','25mg','bid','2022-01-10','2026-08-12'),  -- dose raised 08-12
 ('P-008','celecoxib','200mg','qd prn','2026-07-01',NULL),
 ('P-008','calcium/vitamin D','600mg/800IU','qd','2026-07-01',NULL),
 ('P-009','donepezil','10mg','qd','2021-06-01',NULL),
 ('P-009','melatonin','3mg','qhs','2024-02-01',NULL),
 ('P-010','oxycodone SR','20mg','bid','2026-08-12',NULL),
 ('P-010','ondansetron','4mg','q8h prn','2026-08-12',NULL),
 ('P-010','sennosides','2 tabs','qhs','2026-08-12',NULL);

INSERT INTO physician_orders VALUES
 ('P-001','Harbor Internal Medicine (fictional)','2026-02-14','2026-08-13','Home health certification'),
 ('P-002','Cedar Ridge Hospital (fictional)',    '2026-03-01','2026-08-31','Home health certification'),
 ('P-003','Harbor Internal Medicine (fictional)','2026-06-20','2026-12-19','Home health certification'),
 ('P-004','Eastgate Rehabilitation (fictional)', '2026-02-28','2026-08-27','Home health certification'),
 ('P-005','Cedar Ridge Hospital (fictional)',    '2026-08-01','2026-08-14','Short-term skilled nursing order'),
 ('P-006','Whitfield Clinic (fictional)',        '2026-05-10','2026-11-09','Home health certification'),
 ('P-007','Eastgate Rehabilitation (fictional)', '2026-01-31','2026-07-30','Home health certification'),
 ('P-008','Whitfield Clinic (fictional)',        '2026-07-15','2027-01-14','Home health certification'),
 ('P-009','Harbor Internal Medicine (fictional)','2026-03-09','2026-09-08','Home health certification'),
 ('P-010','Cedar Ridge Hospital (fictional)',    '2026-08-05','2026-08-18','Short-term skilled nursing order');

-- patterns (weekday: 1=Mon .. 5=Fri)
INSERT INTO visit_patterns(patient, weekday, clinician, purpose, interval_weeks, active_from) VALUES
 ('P-001', 1, 'Dr-A', 'weekly skilled nursing', 1,    '2026-08-01'),
 ('P-008', 1, 'Dr-B', 'rehab progress check', 2,   '2026-08-01'),
 ('P-003', 2, 'Dr-A', 'weekly skilled nursing', 1,    '2026-08-01'),
 ('P-006', 2, 'Dr-C', 'weekly skilled nursing', 1,    '2026-08-01'),
 ('P-005', 3, 'Dr-B', 'post-discharge follow-up', 1,  '2026-08-01'),
 ('P-007', 4, 'Dr-A', 'anticoagulation check', 1,     '2026-08-01'),
 ('P-002', 5, 'Dr-B', 'diabetes management', 1,       '2026-08-01'),
 ('P-010', 5, 'Dr-A', 'palliative symptom review', 1, '2026-08-22'),
 ('P-004', 1, 'Dr-C', 'weekly skilled nursing', 1,    '2026-08-01'),
 ('P-009', 1, 'Dr-A', 'caregiver support visit', 1,   '2026-08-01');

-- Past instances only. FUTURE VISITS ARE NOT SEEDED: Troupe's pulse plans them
-- from the patterns (plan_visits) - expansion of an agreed pattern is bookkeeping.
INSERT INTO visits(pattern_id, visit_date, patient, clinician, purpose, status)
SELECT p.id, d::date, p.patient, p.clinician, p.purpose, 'done'
FROM visit_patterns p,
     generate_series(DATE '2026-08-03', DATE '2026-08-23', INTERVAL '1 day') d
WHERE EXTRACT(dow FROM d) = p.weekday
  AND d::date >= p.active_from
  AND (((d::date - p.active_from) / 7) % p.interval_weeks) = 0;

-- one ad-hoc visit: P-010's palliative intake after admission (no pattern behind it)
INSERT INTO visits(pattern_id, visit_date, patient, clinician, purpose, status)
VALUES (NULL, '2026-08-18', 'P-010', 'Dr-A', 'palliative intake', 'done');

-- P-001 acute week: three EXTRA planned visits after a decompensation (08-19..21).
-- Four visit fees land in one week - the fourth is exactly what the weekly cap flags.
INSERT INTO visits(pattern_id, visit_date, patient, clinician, purpose, status, kind) VALUES
 (NULL, '2026-08-19', 'P-001', 'Dr-A', 'acute CHF follow-up', 'done', 'regular'),
 (NULL, '2026-08-20', 'P-001', 'Dr-A', 'acute CHF follow-up', 'done', 'regular'),
 (NULL, '2026-08-21', 'P-001', 'Dr-A', 'acute CHF follow-up', 'done', 'regular');

-- P-007 urgent call on a scheduled-visit day (08-13 evening) - the same-day
-- exclusivity between an urgent call and a regular visit fee needs a ruling.
INSERT INTO visits(pattern_id, visit_date, patient, clinician, purpose, status, kind)
VALUES (NULL, '2026-08-13', 'P-007', 'Dr-A', 'urgent call - palpitations', 'done', 'urgent');

-- ========== seed: signed notes (history, oldest first per patient) ==========

INSERT INTO clinical_notes(patient, note_date, clinician, s, o, a, p, signed_at) VALUES
 -- P-001: weight trend improving under diuretic
 ('P-001','2026-08-03','Dr-A',
  '"I get puffed climbing to the mailbox. Sleeping on two pillows."',
  'BP 138/82, HR 76 reg, wt 62.1kg, crackles both bases, +2 pitting edema to mid-shin',
  'CHF symptomatic. Fluid overloaded relative to baseline.',
  'Reinforce fluid restriction 1.5L. Daily weights. Review diuretic response next visit.',
  '2026-08-03 17:10+09'),
 ('P-001','2026-08-10','Dr-A',
  '"Less puffed this week. Still two pillows at night."',
  'BP 134/80, HR 74 reg, wt 61.6kg (-0.5), scattered basal crackles, +1-2 edema to ankles',
  'Responding to regimen. Congestion improving.',
  'Continue regimen. Confirm daughter bought the scale. Recheck weight trend.',
  '2026-08-10 16:55+09'),
 ('P-001','2026-08-17','Dr-A',
  '"Sleeping better this week. Ankles less puffy in the morning."',
  'BP 132/78, HR 72 reg, wt 61.2kg (-0.4), lungs clear, +1 pitting edema bilateral ankles',
  'CHF stable. Diuretic dose appears adequate. Adherent to fluid restriction.',
  'Continue current regimen. Recheck weight trend next visit. Daughter to buy bathroom scale with larger display.',
  '2026-08-17 17:20+09'),
 -- P-003: before and after the fall
 ('P-003','2026-08-04','Dr-A',
  '"Slow getting out of chairs." Spouse: night-time bathroom trips increasing.',
  'BP 122/74 sitting, 110/68 standing. Gait slow, short steps, no freezing observed today.',
  'Orthostatic tendency. Mobility declining slowly.',
  'Encourage slow position changes. Discuss rug and lighting at home next visit.',
  '2026-08-04 15:40+09'),
 ('P-003','2026-08-11','Dr-A',
  '"Freezing more often when turning in the kitchen." Spouse worried about night-time bathroom trips.',
  'BP 118/70 sitting, 102/64 standing. Gait: short steps, freezing on turns. Bruise left hip, resolving.',
  'Orthostatic drop present. Fall risk elevated - night navigation is the pattern.',
  'PT referral for gait. Remove hallway rug (spouse agreed). Night light for bathroom route. Reassess orthostatics next visit.',
  '2026-08-11 16:05+09'),
 -- P-005: post-discharge recovery, SpO2 improving
 ('P-005','2026-08-12','Dr-B',
  '"Still weak. The hospital wants me on the oxygen every night."',
  'SpO2 91% room air at rest, 86% after 10m walk. RR 24. Diffuse wheeze, prolonged expiration.',
  'Early post-exacerbation. Significant exertional desaturation.',
  'Start night O2 2L as ordered. Prednisone taper per schedule. Limit exertion. Recheck SpO2 trend.',
  '2026-08-12 14:30+09'),
 ('P-005','2026-08-19','Dr-B',
  '"Breathing easier than before the hospital. The night oxygen takes getting used to."',
  'SpO2 93% room air at rest, 89% after hallway walk. RR 20. Breath sounds: distant, scattered wheeze right base.',
  'Post-exacerbation, recovering on expected course. Desaturation on exertion persists.',
  'Finish prednisone taper as scheduled. Reinforce inhaler technique (observed - adequate). Monitor night O2 compliance. Call MD if SpO2 <88% at rest.',
  '2026-08-19 15:15+09'),
 -- P-002
 ('P-002','2026-08-14','Dr-B',
  '"Feet tingle at night, same as before. Sugars have been behaving."',
  'FBG log 98-142 mg/dL over 2 weeks. Feet: skin intact, pulses present, monofilament reduced bilaterally.',
  'Glycaemic control acceptable. Neuropathy stable; skin integrity maintained.',
  'Continue regimen. Reinforce daily foot checks. Recheck A1c due September.',
  '2026-08-14 11:20+09'),
 -- P-007: before and after dose change
 ('P-007','2026-08-06','Dr-A',
  '"Heart raced twice this week, a minute or two each."',
  'HR 96-104 irregularly irregular during episode by patient count. No bruising.',
  'Rate control marginal on current dose.',
  'Flag palpitation episodes to MD - dose review requested. Continue apixaban.',
  '2026-08-06 10:15+09'),
 ('P-007','2026-08-13','Dr-A',
  '"No new bruising. I take the blood thinner with breakfast and dinner like clockwork."',
  'HR 88 irregularly irregular. No bruising or bleeding signs. Pill count consistent with adherence.',
  'AF rate-controlled on increased metoprolol dose. Anticoagulation adherence good.',
  'Continue apixaban and metoprolol 50mg. Renewal of physician order is pending - flagged to office.',
  '2026-08-13 10:40+09'),
 -- P-001 acute week (08-19..21): decompensation after the stable 08-17 note
 ('P-001','2026-08-19','Dr-A',
  'Daughter called: "ankles ballooned overnight, short of breath on the stairs." Ate salted fish gifts over the weekend.',
  'BP 146/88, HR 84 reg, wt 63.0kg (+1.8 from 08-17), crackles both bases, +3 pitting edema to knees',
  'Acute CHF decompensation on dietary sodium load.',
  'Double furosemide for 3 days per standing protocol. Daily visits while decompensated. Strict fluid restriction.',
  '2026-08-19 11:30+09'),
 ('P-001','2026-08-20','Dr-A',
  '"Passed a lot of water since yesterday. Breathing a bit easier lying down."',
  'BP 140/84, HR 80 reg, wt 62.4kg (-0.6), crackles reduced, +2 edema to mid-shin',
  'Responding to increased diuretic. Still congested.',
  'Continue doubled dose. Recheck tomorrow. Daughter staying over this week.',
  '2026-08-20 10:50+09'),
 ('P-001','2026-08-21','Dr-A',
  '"Much better. Slept flat for the first time this week."',
  'BP 136/80, HR 76 reg, wt 61.8kg (-0.6), lungs nearly clear, +1 edema ankles',
  'Decompensation resolving. Diuretic response good.',
  'Taper back to usual dose from tomorrow. Return to weekly schedule. Sodium counselling with daughter done.',
  '2026-08-21 11:05+09'),
 -- P-004 & P-009 (Nagisa Court): two signed Mondays each - the same-building
 -- pair and the 2-visit monthly tier both need signed facts to derive from
 ('P-004','2026-08-10','Dr-C',
  '"The right hand is slow but I can hold the rail now."',
  'BP 128/76. Right grip weak, unchanged. Transfers with one-person assist, steadier than July.',
  'Stroke sequelae stable. Rehab gains holding.',
  'Continue facility rehab plan. Review clopidogrel adherence with staff.',
  '2026-08-10 14:20+09'),
 ('P-004','2026-08-17','Dr-C',
  'Staff: "walked the corridor twice with the frame this week."',
  'BP 126/74. Gait with frame, supervised, 20m without rest.',
  'Functional trajectory improving. No new deficits.',
  'Continue plan. Fall-precaution review with facility staff done.',
  '2026-08-17 14:35+09'),
 ('P-009','2026-08-10','Dr-A',
  'Staff: "quiet week, eating well, naps often."',
  'Calm, oriented to person only. Skin intact. Weight stable.',
  'Advanced dementia, stable. No behavioural crises.',
  'Continue routine. Family visit encouraged this weekend.',
  '2026-08-10 15:05+09'),
 ('P-009','2026-08-17','Dr-A',
  'Staff: "restless at dusk two evenings, settled with routine."',
  'Calm during visit. Hydration adequate. No pressure areas.',
  'Sundowning episodes, mild - no medication change warranted.',
  'Evening routine reinforced with staff. Melatonin timing reviewed. Comprehensive support this month.',
  '2026-08-17 15:20+09'),
 -- P-010: palliative baseline
 ('P-010','2026-08-18','Dr-A',
  'Wife reports pain "mostly 3-4 out of 10, worse late afternoon." Appetite small but present.',
  'Alert, comfortable at rest. Abdomen soft. Bowel movement yesterday (on sennosides).',
  'Pain partially controlled on current SR dose; afternoon breakthrough pattern.',
  'Discuss breakthrough dosing with palliative MD. Continue bowel regimen. Reassess pain diary next visit.',
  '2026-08-18 13:50+09');

INSERT INTO condition_events VALUES
 ('P-003','2026-08-02','fall at home - tripped on hallway rug at night, no fracture, bruised left hip'),
 ('P-005','2026-08-08','discharged from Cedar Ridge Hospital after 5-day admission for COPD exacerbation; new night oxygen 2L'),
 ('P-007','2026-08-12','medication change - metoprolol increased from 25mg to 50mg bid'),
 ('P-010','2026-08-12','admitted to service - new palliative course'),
 ('P-005','2026-08-14','short-term skilled nursing order expired; successor order status unknown');

-- ========== seed: Nagisa Schedule master (ALL FICTIONAL) ==========

INSERT INTO fee_schedule(code, name, kind, points, price_yen, unit, weekly_cap, note) VALUES
 ('NV01','Home visit — single home',            'visit',   800, NULL, 'per_day',   3, 'weekly cap 3; a 4th in the same week needs a human ruling'),
 ('NV02','Home visit — same building',          'visit',   200, NULL, 'per_day',   3, 'applies when 2+ patients of one building are seen the same day'),
 ('NO01','Urgent house call',                   'oncall',  650, NULL, 'per_event', NULL, 'exclusive with a regular visit fee on the same day'),
 ('NC01','Monthly care management — 2+ visits', 'monthly', 4200, NULL,'per_month', NULL, 'auto tier by visit count'),
 ('NC02','Monthly care management — 2+ visits, shared building','monthly',2600,NULL,'per_month',NULL,'2+ managed patients in one building'),
 ('NC03','Monthly care management — 1 visit',   'monthly', 2100, NULL,'per_month', NULL, ''),
 ('NC04','Monthly care management — severe, 2+ visits','monthly',5000,NULL,'per_month',NULL,'severe designation'),
 ('NA02','Extended visit add-on (over 60 min)', 'addon',   100, NULL, 'per_day',   NULL, ''),
 ('NA04','Comprehensive support add-on',        'addon',   130, NULL, 'per_month', NULL, 'once a month'),
 ('NP01','IV drip infusion',                    'act',      50, NULL, 'per_day',   NULL, ''),
 ('NP02','Subcutaneous injection',              'act',      22, NULL, 'per_event', NULL, ''),
 ('NP03','Blood draw',                          'act',      40, NULL, 'per_event', NULL, ''),
 ('NX01','Home oxygen management',              'act',    2200, NULL, 'per_month', NULL, 'once a month'),
 ('NX02','Oxygen concentrator provision',       'act',    3800, NULL, 'per_quarter', NULL, 'once per 3 months'),
 ('ND01','furosemide 20mg — day',               'drug',   NULL, 9.80, 'per_event', NULL, '15 yen or less = 1 point'),
 ('ND02','levodopa/carbidopa 100/25 — day',     'drug',   NULL, 21.50,'per_event', NULL, 'yen/10, go-sha-go-cho-nyu'),
 ('ND03','apixaban 5mg — day',                  'drug',   NULL, 244.50,'per_event',NULL, ''),
 ('ND04','oxycodone SR 20mg — day',             'drug',   NULL, 310.40,'per_event',NULL, ''),
 ('NB01','IV infusion set',                     'material',NULL, 120.00,'per_event',NULL,'yen/10, rounded');

-- ========== seed: services entered at the bedside (August, on signed visits) ==========

INSERT INTO visit_services(visit_id, code, qty, recorded_by)
SELECT v.id, s.code, s.qty, v.clinician
FROM visits v
JOIN (VALUES
  ('P-001','2026-08-17','ND01', 7),
  ('P-001','2026-08-17','NP03', 1),
  ('P-001','2026-08-19','NP01', 1),
  ('P-001','2026-08-19','NB01', 1),
  ('P-001','2026-08-19','ND01', 3),
  ('P-003','2026-08-11','ND02', 7),
  ('P-003','2026-08-11','NP03', 1),
  ('P-005','2026-08-12','NX01', 1),
  ('P-005','2026-08-12','NX02', 1),
  ('P-007','2026-08-06','ND03', 7),
  ('P-007','2026-08-13','NP03', 1),
  ('P-009','2026-08-17','NA04', 1),
  ('P-010','2026-08-18','ND04', 7),
  ('P-010','2026-08-18','NA02', 1)
) AS s(patient, day, code, qty)
  ON s.patient = v.patient AND s.day::date = v.visit_date AND v.kind = 'regular';

-- ========== seed: July, imported pre-Troupe as CONFIRMED legacy ==========
-- The month was billed on the old system; it arrives as locked fact - which is
-- also what lets the submission-file and invoice views show a finished month.

INSERT INTO charges(patient, month, day, visit_id, code, qty, points, status)
SELECT p.code, '2026-07', d::date, NULL, 'NV01', 1, 800, 'derived'
FROM patients p
JOIN (VALUES
  ('P-001','2026-07-06'),('P-001','2026-07-13'),('P-001','2026-07-20'),('P-001','2026-07-27'),
  ('P-002','2026-07-03'),('P-002','2026-07-17'),('P-002','2026-07-31'),
  ('P-003','2026-07-07'),('P-003','2026-07-14'),('P-003','2026-07-21'),('P-003','2026-07-28'),
  ('P-006','2026-07-07'),('P-006','2026-07-21'),
  ('P-007','2026-07-02'),('P-007','2026-07-16'),('P-007','2026-07-30'),
  ('P-008','2026-07-06'),('P-008','2026-07-20')
) AS lv(code, d) ON lv.code = p.code;

INSERT INTO charges(patient, month, day, visit_id, code, qty, points, status)
SELECT c.patient, '2026-07', MAX(c.day), NULL,
       CASE WHEN COUNT(*) >= 2 THEN 'NC01' ELSE 'NC03' END,
       1, CASE WHEN COUNT(*) >= 2 THEN 4200 ELSE 2100 END, 'derived'
FROM charges c WHERE c.month = '2026-07' GROUP BY c.patient;

INSERT INTO claims(patient, month, status, total_points, copay_rate, copay_yen, confirmed_by, confirmed_at)
SELECT c.patient, '2026-07', 'confirmed', SUM(c.points), p.copay_rate,
       (((SUM(c.points) * p.copay_rate + 5) / 10) * 10)::int,   -- 点×10円×割/10、10円未満四捨五入
       'Director', '2026-08-05 09:00+09'
FROM charges c JOIN patients p ON p.code = c.patient
WHERE c.month = '2026-07'
GROUP BY c.patient, p.copay_rate;

-- link each signed note to the visit it documents (same patient, same day, done)
UPDATE clinical_notes n
SET visit_id = v.id
FROM (
  SELECT DISTINCT ON (patient, visit_date) id, patient, visit_date
  FROM visits WHERE status = 'done'
  ORDER BY patient, visit_date, pattern_id NULLS LAST
) v
WHERE v.patient = n.patient AND v.visit_date = n.note_date;

-- P-007 urgent-call note: two visits share the date, so this one is linked explicitly
INSERT INTO clinical_notes(patient, visit_id, note_date, clinician, s, o, a, p, signed_at)
SELECT 'P-007', v.id, '2026-08-13', 'Dr-A',
  'Evening call from spouse: "his heart is racing again and he looks pale."',
  'HR 118 irregularly irregular on arrival, BP 104/68, settled to HR 92 over 40 min observation.',
  'Paroxysmal AF episode, self-terminated. No hemodynamic compromise.',
  'Observed until stable. Reviewed evening dose timing. MD informed same evening.',
  '2026-08-13 20:40+09'
FROM visits v
WHERE v.patient = 'P-007' AND v.visit_date = '2026-08-13' AND v.kind = 'urgent';

-- 紐付け（移行）が済んでから、不変の錠を掛ける
-- 署名済みは不変——憲法を DB 自身に執行させる（書き換え・削除はどの接続にもできない）
CREATE FUNCTION clinical_notes_immutable() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'clinical_notes is append-only: signed records are immutable';
END $$ LANGUAGE plpgsql;
CREATE TRIGGER clinical_notes_no_update BEFORE UPDATE OR DELETE ON clinical_notes
  FOR EACH ROW EXECUTE FUNCTION clinical_notes_immutable();

-- 確定した請求とその月の算定行は不変——確定は人の判断、錠は DB 自身が掛ける
CREATE FUNCTION billing_locked() RETURNS trigger AS $$
BEGIN
  IF TG_TABLE_NAME = 'claims' THEN
    IF OLD.status = 'confirmed' THEN
      RAISE EXCEPTION 'claims: a confirmed claim is immutable';
    END IF;
    RETURN COALESCE(NEW, OLD);
  END IF;
  IF EXISTS (SELECT 1 FROM claims cl
             WHERE cl.patient = OLD.patient AND cl.month = OLD.month
               AND cl.status = 'confirmed') THEN
    RAISE EXCEPTION 'charges: the claim for this month is confirmed - lines are locked';
  END IF;
  RETURN COALESCE(NEW, OLD);
END $$ LANGUAGE plpgsql;
CREATE TRIGGER claims_confirmed_locked BEFORE UPDATE OR DELETE ON claims
  FOR EACH ROW EXECUTE FUNCTION billing_locked();
CREATE TRIGGER charges_confirmed_locked BEFORE UPDATE OR DELETE ON charges
  FOR EACH ROW EXECUTE FUNCTION billing_locked();

-- 確定した月へは新しい算定行も入らない(INSERT は NEW を見る別の門)
CREATE FUNCTION charges_no_insert_into_confirmed() RETURNS trigger AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM claims cl
             WHERE cl.patient = NEW.patient AND cl.month = NEW.month
               AND cl.status = 'confirmed') THEN
    RAISE EXCEPTION 'charges: the claim for this month is confirmed - no new lines';
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER charges_confirmed_no_insert BEFORE INSERT ON charges
  FOR EACH ROW EXECUTE FUNCTION charges_no_insert_into_confirmed();

-- 行為の記帳は署名前だけ——器の検査に加えて DB 自身も守る(競り合いを断つ)
CREATE FUNCTION services_frozen_by_signing() RETURNS trigger AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM visits v
             WHERE v.id = COALESCE(NEW.visit_id, OLD.visit_id)
               AND v.status <> 'scheduled') THEN
    RAISE EXCEPTION 'visit_services: the visit is no longer scheduled - services are frozen';
  END IF;
  RETURN COALESCE(NEW, OLD);
END $$ LANGUAGE plpgsql;
CREATE TRIGGER services_frozen BEFORE INSERT OR UPDATE OR DELETE ON visit_services
  FOR EACH ROW EXECUTE FUNCTION services_frozen_by_signing();
