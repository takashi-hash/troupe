-- EMR (electronic medical record) - Riverbend Home Health (fictional agency)
-- NOTE: Entirely synthetic. No real patient, clinician, practice or visit exists here.
-- This is the agency's system of record that Troupe READS through the source ACL.
-- Troupe never writes here - drafts go to its own ledger and a nurse signs elsewhere.

DROP TABLE IF EXISTS condition_events, visit_notes, visits, physician_orders, medications, patients CASCADE;

CREATE TABLE patients(
  code TEXT PRIMARY KEY,
  age INTEGER NOT NULL,
  living_situation TEXT NOT NULL,
  primary_dx TEXT NOT NULL
);

CREATE TABLE medications(
  patient TEXT NOT NULL REFERENCES patients(code),
  drug TEXT NOT NULL,
  dose TEXT NOT NULL,
  frequency TEXT NOT NULL
);

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
  purpose TEXT NOT NULL
);

CREATE TABLE visit_notes(
  patient TEXT NOT NULL REFERENCES patients(code),
  note_date DATE NOT NULL,
  nurse TEXT NOT NULL,
  s TEXT NOT NULL, o TEXT NOT NULL, a TEXT NOT NULL, p TEXT NOT NULL
);

CREATE TABLE condition_events(
  patient TEXT NOT NULL REFERENCES patients(code),
  event_date DATE NOT NULL,
  description TEXT NOT NULL
);

INSERT INTO patients VALUES
 ('P-001', 82, 'lives alone, daughter visits weekends',        'congestive heart failure, NYHA II'),
 ('P-002', 74, 'lives with spouse',                            'type 2 diabetes with peripheral neuropathy'),
 ('P-003', 76, 'lives with spouse',                            'Parkinson''s disease, Hoehn-Yahr 3'),
 ('P-004', 88, 'assisted living apartment',                    'stroke sequelae, right hemiparesis'),
 ('P-005', 68, 'lives with son''s family',                     'COPD GOLD III, recent exacerbation'),
 ('P-006', 79, 'lives alone, neighbour checks in',             'chronic kidney disease stage 4'),
 ('P-007', 84, 'lives with spouse',                            'atrial fibrillation on anticoagulation'),
 ('P-008', 71, 'lives alone',                                  'post hip replacement rehabilitation'),
 ('P-009', 90, 'lives with daughter',                          'advanced dementia, comfort-focused care'),
 ('P-010', 66, 'lives with spouse',                            'metastatic colon cancer, palliative course');

INSERT INTO medications VALUES
 ('P-001','furosemide','20mg','qd'), ('P-001','lisinopril','10mg','qd'), ('P-001','aspirin','81mg','qd'),
 ('P-002','metformin','500mg','bid'), ('P-002','insulin glargine','12u','qhs'), ('P-002','gabapentin','300mg','tid'),
 ('P-003','levodopa/carbidopa','100/25','tid'), ('P-003','rasagiline','1mg','qd'),
 ('P-004','clopidogrel','75mg','qd'), ('P-004','atorvastatin','40mg','qd'),
 ('P-005','tiotropium','18mcg','qd'), ('P-005','salmeterol-fluticasone','50/500','bid'), ('P-005','prednisone taper','per schedule','ends 2026-08-25'),
 ('P-006','sevelamer','800mg','tid with meals'), ('P-006','darbepoetin','40mcg','weekly'),
 ('P-007','apixaban','5mg','bid'), ('P-007','metoprolol','50mg','bid'),
 ('P-008','celecoxib','200mg','qd prn'), ('P-008','calcium/vitamin D','600mg/800IU','qd'),
 ('P-009','donepezil','10mg','qd'), ('P-009','melatonin','3mg','qhs'),
 ('P-010','oxycodone SR','20mg','bid'), ('P-010','ondansetron','4mg','q8h prn'), ('P-010','sennosides','2 tabs','qhs');

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

INSERT INTO visits VALUES
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

INSERT INTO visit_notes VALUES
 ('P-001','2026-08-17','RN-A',
  '"Sleeping better this week. Ankles less puffy in the morning."',
  'BP 132/78, HR 72 reg, wt 61.2kg (-0.4), lungs clear, +1 pitting edema bilateral ankles',
  'CHF stable. Diuretic dose appears adequate. Adherent to fluid restriction.',
  'Continue current regimen. Recheck weight trend next visit. Daughter to buy bathroom scale with larger display.'),
 ('P-003','2026-08-11','RN-A',
  '"Freezing more often when turning in the kitchen." Spouse worried about night-time bathroom trips.',
  'BP 118/70 sitting, 102/64 standing. Gait: short steps, freezing on turns. Bruise left hip, resolving.',
  'Orthostatic drop present. Fall risk elevated - night navigation is the pattern.',
  'PT referral for gait. Remove hallway rug (spouse agreed). Night light for bathroom route. Reassess orthostatics next visit.'),
 ('P-005','2026-08-19','RN-B',
  '"Breathing easier than before the hospital. The night oxygen takes getting used to."',
  'SpO2 93% room air at rest, 89% after hallway walk. RR 20. Breath sounds: distant, scattered wheeze right base.',
  'Post-exacerbation, recovering on expected course. Desaturation on exertion persists.',
  'Finish prednisone taper as scheduled. Reinforce inhaler technique (observed - adequate). Monitor night O2 compliance. Call MD if SpO2 <88% at rest.'),
 ('P-002','2026-08-14','RN-B',
  '"Feet tingle at night, same as before. Sugars have been behaving."',
  'FBG log 98-142 mg/dL over 2 weeks. Feet: skin intact, pulses present, monofilament reduced bilaterally.',
  'Glycaemic control acceptable. Neuropathy stable; skin integrity maintained.',
  'Continue regimen. Reinforce daily foot checks. Recheck A1c due September.'),
 ('P-007','2026-08-13','RN-A',
  '"No new bruising. I take the blood thinner with breakfast and dinner like clockwork."',
  'HR 88 irregularly irregular. No bruising or bleeding signs. Pill count consistent with adherence.',
  'AF rate-controlled on current dose. Anticoagulation adherence good.',
  'Continue apixaban and metoprolol. Renewal of physician order is pending - flagged to office.'),
 ('P-010','2026-08-18','RN-A',
  'Wife reports pain "mostly 3-4 out of 10, worse late afternoon." Appetite small but present.',
  'Alert, comfortable at rest. Abdomen soft. Bowel movement yesterday (on sennosides).',
  'Pain partially controlled on current SR dose; afternoon breakthrough pattern.',
  'Discuss breakthrough dosing with palliative MD. Continue bowel regimen. Reassess pain diary next visit.');

INSERT INTO condition_events VALUES
 ('P-003','2026-08-02','fall at home - tripped on hallway rug at night, no fracture, bruised left hip'),
 ('P-005','2026-08-08','discharged from Cedar Ridge Hospital after 5-day admission for COPD exacerbation; new night oxygen 2L'),
 ('P-007','2026-08-12','medication change - metoprolol increased from 25mg to 50mg bid'),
 ('P-010','2026-08-12','admitted to service - new palliative course'),
 ('P-005','2026-08-14','short-term skilled nursing order expired; successor order status unknown');
