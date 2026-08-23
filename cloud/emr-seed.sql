-- EMR (electronic medical record) - Riverbend Home Health (fictional agency)
-- NOTE: Entirely synthetic. No real patient, clinician, practice or visit exists here.
--
-- Master data (slow-changing) and clinical data (event streams) are kept apart.
-- clinical_notes holds SIGNED (final) notes only - append-only, never edited.
-- note_drafts is the draft inbox: Troupe deposits approved drafts here, a nurse
-- rewrites and signs elsewhere. Troupe has no path that writes a signed note.

DROP TABLE IF EXISTS note_drafts, clinical_notes, visit_notes, condition_events,
  visits, physician_orders, medications, patient_conditions, patients CASCADE;

-- ========== master ==========

CREATE TABLE patients(
  code TEXT PRIMARY KEY,
  age INTEGER NOT NULL,
  living_situation TEXT NOT NULL
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

CREATE TABLE visits(
  visit_date DATE NOT NULL,
  patient TEXT NOT NULL REFERENCES patients(code),
  nurse TEXT NOT NULL,
  purpose TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled','done'))
);

CREATE TABLE clinical_notes(          -- SIGNED notes only. Append-only.
  id BIGSERIAL PRIMARY KEY,
  patient TEXT NOT NULL REFERENCES patients(code),
  note_date DATE NOT NULL,
  nurse TEXT NOT NULL,
  s TEXT NOT NULL, o TEXT NOT NULL, a TEXT NOT NULL, p TEXT NOT NULL,
  signed_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE note_drafts(             -- the draft inbox. Troupe writes here and only here.
  id BIGSERIAL PRIMARY KEY,
  patient TEXT NOT NULL REFERENCES patients(code),
  body TEXT NOT NULL,
  based_on_job TEXT NOT NULL UNIQUE,  -- idempotency: one deposit per approved job
  delivered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE condition_events(
  patient TEXT NOT NULL REFERENCES patients(code),
  event_date DATE NOT NULL,
  description TEXT NOT NULL
);

-- ========== seed: master ==========

INSERT INTO patients VALUES
 ('P-001', 82, 'lives alone, daughter visits weekends'),
 ('P-002', 74, 'lives with spouse'),
 ('P-003', 76, 'lives with spouse'),
 ('P-004', 88, 'assisted living apartment'),
 ('P-005', 68, 'lives with son''s family'),
 ('P-006', 79, 'lives alone, neighbour checks in'),
 ('P-007', 84, 'lives with spouse'),
 ('P-008', 71, 'lives alone'),
 ('P-009', 90, 'lives with daughter'),
 ('P-010', 66, 'lives with spouse');

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

INSERT INTO visits(visit_date, patient, nurse, purpose) VALUES
 ('2026-08-24','P-001','RN-A','weekly skilled nursing'),
 ('2026-08-24','P-008','RN-B','rehab progress check'),
 ('2026-08-25','P-003','RN-A','weekly skilled nursing'),
 ('2026-08-25','P-006','RN-C','weekly skilled nursing'),
 ('2026-08-26','P-005','RN-B','post-discharge follow-up'),
 ('2026-08-27','P-007','RN-A','anticoagulation check'),
 ('2026-08-28','P-002','RN-B','diabetes management'),
 ('2026-08-28','P-010','RN-A','palliative symptom review'),
 ('2026-08-31','P-004','RN-C','weekly skilled nursing'),
 ('2026-08-31','P-009','RN-A','caregiver support visit');

-- ========== seed: signed notes (history, oldest first per patient) ==========

INSERT INTO clinical_notes(patient, note_date, nurse, s, o, a, p, signed_at) VALUES
 -- P-001: weight trend improving under diuretic
 ('P-001','2026-08-03','RN-A',
  '"I get puffed climbing to the mailbox. Sleeping on two pillows."',
  'BP 138/82, HR 76 reg, wt 62.1kg, crackles both bases, +2 pitting edema to mid-shin',
  'CHF symptomatic. Fluid overloaded relative to baseline.',
  'Reinforce fluid restriction 1.5L. Daily weights. Review diuretic response next visit.',
  '2026-08-03 17:10+09'),
 ('P-001','2026-08-10','RN-A',
  '"Less puffed this week. Still two pillows at night."',
  'BP 134/80, HR 74 reg, wt 61.6kg (-0.5), scattered basal crackles, +1-2 edema to ankles',
  'Responding to regimen. Congestion improving.',
  'Continue regimen. Confirm daughter bought the scale. Recheck weight trend.',
  '2026-08-10 16:55+09'),
 ('P-001','2026-08-17','RN-A',
  '"Sleeping better this week. Ankles less puffy in the morning."',
  'BP 132/78, HR 72 reg, wt 61.2kg (-0.4), lungs clear, +1 pitting edema bilateral ankles',
  'CHF stable. Diuretic dose appears adequate. Adherent to fluid restriction.',
  'Continue current regimen. Recheck weight trend next visit. Daughter to buy bathroom scale with larger display.',
  '2026-08-17 17:20+09'),
 -- P-003: before and after the fall
 ('P-003','2026-08-04','RN-A',
  '"Slow getting out of chairs." Spouse: night-time bathroom trips increasing.',
  'BP 122/74 sitting, 110/68 standing. Gait slow, short steps, no freezing observed today.',
  'Orthostatic tendency. Mobility declining slowly.',
  'Encourage slow position changes. Discuss rug and lighting at home next visit.',
  '2026-08-04 15:40+09'),
 ('P-003','2026-08-11','RN-A',
  '"Freezing more often when turning in the kitchen." Spouse worried about night-time bathroom trips.',
  'BP 118/70 sitting, 102/64 standing. Gait: short steps, freezing on turns. Bruise left hip, resolving.',
  'Orthostatic drop present. Fall risk elevated - night navigation is the pattern.',
  'PT referral for gait. Remove hallway rug (spouse agreed). Night light for bathroom route. Reassess orthostatics next visit.',
  '2026-08-11 16:05+09'),
 -- P-005: post-discharge recovery, SpO2 improving
 ('P-005','2026-08-12','RN-B',
  '"Still weak. The hospital wants me on the oxygen every night."',
  'SpO2 91% room air at rest, 86% after 10m walk. RR 24. Diffuse wheeze, prolonged expiration.',
  'Early post-exacerbation. Significant exertional desaturation.',
  'Start night O2 2L as ordered. Prednisone taper per schedule. Limit exertion. Recheck SpO2 trend.',
  '2026-08-12 14:30+09'),
 ('P-005','2026-08-19','RN-B',
  '"Breathing easier than before the hospital. The night oxygen takes getting used to."',
  'SpO2 93% room air at rest, 89% after hallway walk. RR 20. Breath sounds: distant, scattered wheeze right base.',
  'Post-exacerbation, recovering on expected course. Desaturation on exertion persists.',
  'Finish prednisone taper as scheduled. Reinforce inhaler technique (observed - adequate). Monitor night O2 compliance. Call MD if SpO2 <88% at rest.',
  '2026-08-19 15:15+09'),
 -- P-002
 ('P-002','2026-08-14','RN-B',
  '"Feet tingle at night, same as before. Sugars have been behaving."',
  'FBG log 98-142 mg/dL over 2 weeks. Feet: skin intact, pulses present, monofilament reduced bilaterally.',
  'Glycaemic control acceptable. Neuropathy stable; skin integrity maintained.',
  'Continue regimen. Reinforce daily foot checks. Recheck A1c due September.',
  '2026-08-14 11:20+09'),
 -- P-007: before and after dose change
 ('P-007','2026-08-06','RN-A',
  '"Heart raced twice this week, a minute or two each."',
  'HR 96-104 irregularly irregular during episode by patient count. No bruising.',
  'Rate control marginal on current dose.',
  'Flag palpitation episodes to MD - dose review requested. Continue apixaban.',
  '2026-08-06 10:15+09'),
 ('P-007','2026-08-13','RN-A',
  '"No new bruising. I take the blood thinner with breakfast and dinner like clockwork."',
  'HR 88 irregularly irregular. No bruising or bleeding signs. Pill count consistent with adherence.',
  'AF rate-controlled on increased metoprolol dose. Anticoagulation adherence good.',
  'Continue apixaban and metoprolol 50mg. Renewal of physician order is pending - flagged to office.',
  '2026-08-13 10:40+09'),
 -- P-010: palliative baseline
 ('P-010','2026-08-18','RN-A',
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
