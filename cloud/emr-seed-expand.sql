-- ============================================================================
-- emr-seed-expand.sql — 増員の追記シード(P-011..P-022)。ALL DATA SYNTHETIC.
--
-- emr-seed.sql の「再実行」ではない——追記専用。帳簿の配達済み印(DraftDelivered)
-- を焼かないため、emr-seed.sql をもう一度流してはならない。
--
-- 順序の掟(トリガーが生きているDBに入れるため):
--   患者 -> カルテ材料 -> 取り決め -> 過去の訪問を scheduled で
--   -> 行為(visit_services) -> done へ更新 -> 署名済み注記(visit_id を直に紐付け)
--   凍結トリガー services_frozen は「scheduled 以外への記帳」を拒む——行為が先。
--
-- 守っている境界:
--   * 8月より前の日付は1件も入れない(7月の確定6件の物語を増やさない)
--   * 週あたり正規訪問は全員1回(週3上限に誰も触れない。8/30-9/5の継ぎ目週も1回)
--   * 行為は白名単のみ: NP01/NP02/NP03/NA02/NB01/ND03/ND04
--     (NA04/NX01/NX02 は月次・四半期の重複旗の種になるため新患者に入れない)
--   * 往診(urgent)と正規訪問の同日重ねは作らない(P-007の仕込みを唯一に保つ)
--   * 既存患者 P-001..P-010 には一切触れない
-- ============================================================================

BEGIN;

-- 二重実行ガード
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM patients WHERE code = 'P-011') THEN
    RAISE EXCEPTION 'expand seed already applied (P-011 exists)';
  END IF;
END $$;

-- ========== patients (12) ==========
INSERT INTO patients(code, age, living_situation, address, lat, lng, copay_rate, building, severe) VALUES
 ('P-011', 81, 'with daughter',                                    'Umegaoka Sta. (public landmark stand-in)',          35.6567, 139.6539, 1, NULL, false),
 ('P-012', 77, 'lives alone',                                      'Kyodo Sta. (public landmark stand-in)',             35.6528, 139.6363, 2, NULL, false),
 ('P-013', 86, 'with spouse',                                      'Sakura-Shinmachi Sta. (public landmark stand-in)',  35.6337, 139.6450, 1, NULL, false),
 ('P-014', 73, 'with spouse',                                      'Miyanosaka Sta. (public landmark stand-in)',        35.6478, 139.6511, 1, NULL, false),
 ('P-015', 68, 'lives alone',                                      'Yoga Sta. (public landmark stand-in)',              35.6267, 139.6341, 3, NULL, false),
 ('P-016', 89, 'with son',                                         'Hanegi Park (public landmark stand-in)',            35.6607, 139.6497, 1, NULL, false),
 ('P-017', 75, 'with spouse',                                      'Chitose-Funabashi Sta. (public landmark stand-in)', 35.6494, 139.6270, 1, NULL, false),
 ('P-018', 87, 'Tsubaki Grove (fictional care facility), room 105','Roka Koshun-en Gardens (public landmark stand-in)', 35.6553, 139.6157, 1, 'tsubaki-grove', false),
 ('P-019', 92, 'Tsubaki Grove (fictional care facility), room 210','Roka Koshun-en Gardens (public landmark stand-in)', 35.6553, 139.6157, 1, 'tsubaki-grove', false),
 ('P-020', 64, 'with spouse',                                      'Kinuta Park (public landmark stand-in)',            35.6296, 139.6197, 3, NULL, true),
 ('P-021', 79, 'with daughter',                                    'Setagaya-Daita Sta. (public landmark stand-in)',    35.6608, 139.6592, 2, NULL, false),
 ('P-022', 72, 'with daughter',                                    'Komazawa-Daigaku Sta. (public landmark stand-in)',  35.6320, 139.6687, 2, NULL, false);

-- ========== conditions ==========
INSERT INTO patient_conditions(patient, dx, is_primary, onset) VALUES
 ('P-011','chronic respiratory failure from interstitial lung disease, on home oxygen', true,  '2022-05-01'),
 ('P-012','rheumatoid arthritis with advanced joint deformity, housebound',             true,  '2005-03-01'),
 ('P-013','Alzheimer''s dementia, moderate, with behavioural symptoms (BPSD)',          true,  '2021-09-01'),
 ('P-014','amyotrophic lateral sclerosis, limb-onset, early stage',                     true,  '2025-11-01'),
 ('P-015','alcoholic liver cirrhosis Child-Pugh B, recurrent ascites',                  true,  '2020-01-01'),
 ('P-015','atrial fibrillation',                                                        false, '2023-06-01'),
 ('P-016','bedbound frailty with stage III sacral pressure ulcer',                      true,  '2024-02-01'),
 ('P-017','post-gastrectomy, PEG tube feeding, malnutrition',                           true,  '2023-12-01'),
 ('P-018','Lewy body dementia with fluctuating cognition',                              true,  '2022-08-01'),
 ('P-019','multiple cerebral infarctions, bedbound, dysphagia',                         true,  '2019-10-01'),
 ('P-020','metastatic lung cancer, home palliative care',                               true,  '2026-05-01'),
 ('P-021','end-stage COPD, chronic type 2 respiratory failure on home oxygen',          true,  '2018-04-01'),
 ('P-022','stable angina, post-PCI',                                                    true,  '2024-07-01');

-- ========== medications (current) ==========
INSERT INTO medications(patient, drug, dose, frequency, started, stopped) VALUES
 ('P-011','pirfenidone','600mg','tid',            '2023-02-01', NULL),
 ('P-011','omeprazole','20mg','qd',               '2023-02-01', NULL),
 ('P-012','methotrexate','8mg','weekly',          '2010-04-01', NULL),
 ('P-012','folic acid','5mg','weekly',            '2010-04-01', NULL),
 ('P-012','celecoxib','200mg','bid',              '2024-01-01', NULL),
 ('P-013','donepezil','10mg','qd',                '2022-03-01', NULL),
 ('P-013','memantine','20mg','qd',                '2023-05-01', NULL),
 ('P-014','riluzole','50mg','bid',                '2025-12-01', NULL),
 ('P-015','spironolactone','50mg','qd',           '2024-08-01', NULL),
 ('P-015','furosemide','40mg','qd',               '2025-02-01', NULL),
 ('P-015','apixaban','2.5mg','bid',               '2023-07-01', NULL),
 ('P-016','zinc + vitamin C supplement','1 sachet','qd','2026-03-01', NULL),
 ('P-017','pancrelipase','1 sachet','with feeds', '2024-01-01', NULL),
 ('P-017','esomeprazole','20mg','qd',             '2024-01-01', NULL),
 ('P-018','donepezil','5mg','qd',                 '2023-01-01', NULL),
 ('P-018','yokukansan','2.5g','tid',              '2025-06-01', NULL),
 ('P-019','clopidogrel','75mg','qd',              '2019-11-01', NULL),
 ('P-019','amlodipine','5mg','qd',                '2019-11-01', NULL),
 ('P-020','oxycodone SR','20mg','bid',            '2026-06-01', NULL),
 ('P-020','naldemedine','0.2mg','qd',             '2026-06-01', NULL),
 ('P-021','tiotropium','18mcg','qd',              '2019-01-01', NULL),
 ('P-021','salbutamol','100mcg','prn',            '2019-01-01', NULL),
 ('P-022','aspirin','100mg','qd',                 '2024-08-01', NULL),
 ('P-022','clopidogrel','75mg','qd',              '2024-08-01', NULL),
 ('P-022','atorvastatin','10mg','qd',             '2024-08-01', NULL),
 ('P-022','bisoprolol','2.5mg','qd',              '2024-08-01', NULL);

-- ========== physician orders (expiry past judging end — no red chips) ==========
INSERT INTO physician_orders(patient, practice, signed, expires, order_type) VALUES
 ('P-011','Cedar Ridge Hospital (fictional)',  '2026-07-28','2026-12-31','Home medical care order'),
 ('P-012','Maple Gate Clinic (fictional)',     '2026-07-30','2026-12-31','Home medical care order'),
 ('P-013','Westfield General (fictional)',     '2026-07-29','2026-12-31','Home medical care order'),
 ('P-014','Westfield General (fictional)',     '2026-07-31','2026-12-31','Home medical care order'),
 ('P-015','Cedar Ridge Hospital (fictional)',  '2026-08-01','2026-12-31','Home medical care order'),
 ('P-016','Maple Gate Clinic (fictional)',     '2026-08-01','2026-12-31','Home medical care order'),
 ('P-017','Westfield General (fictional)',     '2026-08-02','2026-12-31','Home medical care order'),
 ('P-018','Maple Gate Clinic (fictional)',     '2026-08-03','2026-12-31','Home medical care order'),
 ('P-019','Maple Gate Clinic (fictional)',     '2026-08-03','2026-12-31','Home medical care order'),
 ('P-020','Cedar Ridge Hospital (fictional)',  '2026-08-04','2026-12-31','Home medical care order'),
 ('P-021','Cedar Ridge Hospital (fictional)',  '2026-08-21','2026-12-31','Home medical care order'),
 ('P-022','Westfield General (fictional)',     '2026-08-10','2026-12-31','Home medical care order');

-- ========== chart events (each mentions the term the draft rule anchors on) ==========
INSERT INTO condition_events VALUES
 ('P-011','2026-08-01','home oxygen at 2L at rest; SpO2 at review 93% on oxygen'),
 ('P-012','2026-08-11','joint pain flare in both hands (pain 6/10); morning stiffness 90 minutes'),
 ('P-013','2026-08-09','evening agitation episode (BPSD) — settled with routine, no medication'),
 ('P-014','2026-08-12','grip strength declining on the right; occupational therapy referral placed'),
 ('P-015','2026-08-13','abdominal girth up 2cm in a week — ascites re-accumulating; diuretic dose reviewed'),
 ('P-016','2026-08-06','sacral pressure ulcer staged III at wound review; dressing protocol updated'),
 ('P-017','2026-08-07','PEG site mild redness, no discharge; feed tolerance stable'),
 ('P-018','2026-08-15','visual hallucination episode reported by facility staff (small figures in the room)'),
 ('P-019','2026-08-15','increased suction needs after lunch; swallowing review requested'),
 ('P-020','2026-08-16','breakthrough pain NRS 6 late afternoon; rescue dose used twice'),
 ('P-021','2026-08-21','discharged from Cedar Ridge Hospital (fictional) after COPD exacerbation; home oxygen 2L continued; SpO2 at discharge 92%'),
 ('P-022','2026-08-14','post-PCI review — BP 128/76, no angina since the procedure');

-- ========== agreements (weekday: 0=Sun .. 6=Sat) ==========
INSERT INTO visit_patterns(patient, weekday, clinician, purpose, interval_weeks, active_from) VALUES
 ('P-011', 1, 'Dr-B', 'weekly respiratory management',        1, '2026-08-03'),
 ('P-012', 2, 'Dr-B', 'weekly pain and function management',  1, '2026-08-04'),
 ('P-013', 3, 'Dr-A', 'weekly dementia care support',         1, '2026-08-05'),
 ('P-014', 3, 'Dr-C', 'weekly neuromuscular monitoring',      1, '2026-08-05'),
 ('P-015', 4, 'Dr-B', 'weekly ascites and nutrition check',   1, '2026-08-06'),
 ('P-016', 4, 'Dr-C', 'weekly wound care',                    1, '2026-08-06'),
 ('P-017', 5, 'Dr-C', 'weekly PEG and nutrition management',  1, '2026-08-07'),
 ('P-018', 6, 'Dr-B', 'Saturday facility round — dementia care', 1, '2026-08-08'),
 ('P-019', 6, 'Dr-B', 'Saturday facility round — airway care',   1, '2026-08-08'),
 ('P-020', 0, 'Dr-C', 'Sunday palliative visit — symptom control', 1, '2026-08-09'),
 ('P-022', 5, 'Dr-B', 'monthly post-PCI review',              4, '2026-08-14');
-- P-021 の取り決めはここに無い——今日、窓の取り決めフォームから普通の道で登録する
-- (新規受け入れの生きた実演。脈が日曜 08-30 の初回訪問を1分以内に立てる)

-- ========== past instances, scheduled first (pattern_id を持たせて脈と衝突させない) ==========
INSERT INTO visits(pattern_id, visit_date, patient, clinician, purpose, status)
SELECT p.id, d::date, p.patient, p.clinician, p.purpose, 'scheduled'
FROM visit_patterns p,
     generate_series(DATE '2026-08-03', DATE '2026-08-23', INTERVAL '1 day') d
WHERE p.patient IN ('P-011','P-012','P-013','P-014','P-015','P-016','P-017','P-018','P-019','P-020','P-022')
  AND EXTRACT(dow FROM d) = p.weekday
  AND d::date >= p.active_from
  AND (((d::date - p.active_from) / 7) % p.interval_weeks) = 0;

-- P-011 の往診(土 08-15 夕) — 同日に正規訪問は無い(旗にならない、月内の週上限にも数えない)
INSERT INTO visits(pattern_id, visit_date, patient, clinician, purpose, status, kind)
VALUES (NULL, '2026-08-15', 'P-011', 'Dr-B', 'urgent call — worsening dyspnoea', 'scheduled', 'urgent');

-- ========== bedside services (visits がまだ scheduled のうちに) ==========
INSERT INTO visit_services(visit_id, code, qty, recorded_by)
SELECT v.id, s.code, s.qty, v.clinician
FROM visits v
JOIN (VALUES
  -- P-011: 点滴+ルート一式(毎回)
  ('P-011','2026-08-03','NP01',1),('P-011','2026-08-03','NB01',1),
  ('P-011','2026-08-10','NP01',1),('P-011','2026-08-10','NB01',1),
  ('P-011','2026-08-17','NP01',1),('P-011','2026-08-17','NB01',1),
  -- P-012: 点滴(毎回)+皮下注1回(生物学的製剤の見立て)
  ('P-012','2026-08-04','NP01',1),
  ('P-012','2026-08-11','NP01',1),('P-012','2026-08-11','NP02',1),
  ('P-012','2026-08-18','NP01',1),
  -- P-013: 点滴(毎回)
  ('P-013','2026-08-05','NP01',1),
  ('P-013','2026-08-12','NP01',1),
  ('P-013','2026-08-19','NP01',1),
  -- P-014: 点滴+採血(毎回)
  ('P-014','2026-08-05','NP01',1),('P-014','2026-08-05','NP03',1),
  ('P-014','2026-08-12','NP01',1),('P-014','2026-08-12','NP03',1),
  ('P-014','2026-08-19','NP01',1),('P-014','2026-08-19','NP03',1),
  -- P-015: 点滴(毎回)+アピキサバン7日分1回
  ('P-015','2026-08-06','NP01',1),
  ('P-015','2026-08-13','NP01',1),('P-015','2026-08-13','ND03',7),
  ('P-015','2026-08-20','NP01',1),
  -- P-016: 皮下注+被覆材(毎回)
  ('P-016','2026-08-06','NP02',1),('P-016','2026-08-06','NB01',1),
  ('P-016','2026-08-13','NP02',1),('P-016','2026-08-13','NB01',1),
  ('P-016','2026-08-20','NP02',1),('P-016','2026-08-20','NB01',1),
  -- P-017: 点滴+ルート一式(毎回)
  ('P-017','2026-08-07','NP01',1),('P-017','2026-08-07','NB01',1),
  ('P-017','2026-08-14','NP01',1),('P-017','2026-08-14','NB01',1),
  ('P-017','2026-08-21','NP01',1),('P-017','2026-08-21','NB01',1),
  -- P-018: 点滴(毎回)
  ('P-018','2026-08-08','NP01',1),
  ('P-018','2026-08-15','NP01',1),
  ('P-018','2026-08-22','NP01',1),
  -- P-019: 皮下注+長時間加算(毎回)
  ('P-019','2026-08-08','NP02',1),('P-019','2026-08-08','NA02',1),
  ('P-019','2026-08-15','NP02',1),('P-019','2026-08-15','NA02',1),
  ('P-019','2026-08-22','NP02',1),('P-019','2026-08-22','NA02',1),
  -- P-020: 点滴+オキシコドン1日分(毎回)
  ('P-020','2026-08-09','NP01',1),('P-020','2026-08-09','ND04',1),
  ('P-020','2026-08-16','NP01',1),('P-020','2026-08-16','ND04',1),
  ('P-020','2026-08-23','NP01',1),('P-020','2026-08-23','ND04',1),
  -- P-022: 点滴1回
  ('P-022','2026-08-14','NP01',1)
) AS s(patient, day, code, qty)
  ON s.patient = v.patient AND s.day::date = v.visit_date AND v.kind = 'regular';

-- ========== flip to done (行為の記帳が済んでから) ==========
UPDATE visits SET status = 'done'
WHERE patient IN ('P-011','P-012','P-013','P-014','P-015','P-016','P-017','P-018','P-019','P-020','P-022')
  AND visit_date <= DATE '2026-08-23';

-- ========== signed notes — visit_id を直に紐付けて入れる(算定は紐付いた署名だけを見る) ==========
INSERT INTO clinical_notes(patient, visit_id, note_date, clinician, s, o, a, p, signed_at)
SELECT n.patient, v.id, n.day::date, n.clinician, n.s, n.o, n.a, n.p, n.at::timestamptz
FROM (VALUES
 -- P-011 ILD: SpO2 の推移を追う
 ('P-011','2026-08-03','Dr-B','regular',
  'Daughter: "breathless dressing, manages meals seated." No fever.',
  'SpO2 93% on 2L at rest, 89% after walking to the toilet. RR 22. Fine crackles both bases.',
  'Interstitial lung disease, chronic respiratory failure — stable on oxygen at rest, desaturates on exertion.',
  'Continue 2L at rest, 3L on exertion. Pace activities. Recheck SpO2 trend next visit.',
  '2026-08-03 11:20+09'),
 ('P-011','2026-08-10','Dr-B','regular',
  '"Less breathless this week when I take it slowly."',
  'SpO2 94% on 2L at rest, 90% post-exertion. RR 20. Crackles unchanged.',
  'SpO2 trend stable to slightly improved with pacing. No infection signs.',
  'Continue current oxygen plan. Daughter to log SpO2 morning and evening.',
  '2026-08-10 11:05+09'),
 ('P-011','2026-08-15','Dr-B','urgent',
  'Urgent call 18:40: "suddenly very breathless after supper." Anxious.',
  'SpO2 88% on 2L, rose to 93% on 4L over 20 min. Afebrile. No new focal signs. HR 96.',
  'Acute-on-chronic desaturation, settled with temporary flow increase — likely exertional/anxiety spiral, no infection evidence tonight.',
  'Return to 2L overnight after stable 30 min. Daughter to call if SpO2 below 90% at rest. Review at Monday visit.',
  '2026-08-15 19:35+09'),
 ('P-011','2026-08-17','Dr-B','regular',
  '"Friday scared us. Since then it has been calm."',
  'SpO2 93% on 2L at rest, log shows 92-94% all week except the Friday dip. RR 20.',
  'Back to baseline after the urgent episode. SpO2 log genuinely useful.',
  'Continue oxygen plan and log. Rehearse the 4L rescue steps with daughter. Next review in a week.',
  '2026-08-17 11:15+09'),
 -- P-012 RA: pain を追う
 ('P-012','2026-08-04','Dr-B','regular',
  '"Hands are bad in the morning — pain about 5 out of 10 for the first hour."',
  'MCP joints swollen and tender both hands. Morning stiffness ~60 min. Grip weak but functional.',
  'RA active, pain partially controlled. Housebound — function is the goal.',
  'Continue methotrexate weekly. Review pain diary next visit. Occupational aids list started.',
  '2026-08-04 13:40+09'),
 ('P-012','2026-08-11','Dr-B','regular',
  '"Worse this week — pain 6 out of 10, stiffness most of the morning."',
  'Both hands warmer, MCP swelling up. Stiffness 90 min. Biologic dose given subcutaneously today.',
  'Flare on background RA. Pain up, function down.',
  'Biologic injection given. Ice packs for the mornings. Reassess pain score in one week — escalate if not below 5.',
  '2026-08-11 13:30+09'),
 ('P-012','2026-08-18','Dr-B','regular',
  '"Better. Pain back to 4, mornings shorter."',
  'Swelling receding, stiffness ~45 min. Grip improved vs last week.',
  'Flare settling after the injection. Pain trend downward.',
  'Continue regimen. Keep the pain diary. Next injection per schedule.',
  '2026-08-18 13:35+09'),
 -- P-013 Alzheimer: BPSD を追う
 ('P-013','2026-08-05','Dr-A','regular',
  'Spouse: "evenings are hard — pacing and asking for her mother."',
  'Calm during visit, oriented to person. Eats well. No falls.',
  'Moderate Alzheimer''s with evening BPSD (pacing, repetitive questions). Spouse coping but tired.',
  'Evening routine card for spouse. Day rhythm: light walk after lunch. Review BPSD diary next visit.',
  '2026-08-05 14:10+09'),
 ('P-013','2026-08-12','Dr-A','regular',
  'Spouse: "two rough evenings, otherwise the routine helps."',
  'Calm, redirected easily today. Hydration adequate. Skin intact.',
  'BPSD frequency down with routine — two episodes this week vs nightly before.',
  'Keep routine. Respite day-care leaflet left with spouse. No medication change.',
  '2026-08-12 14:05+09'),
 ('P-013','2026-08-19','Dr-A','regular',
  'Spouse: "one bad evening after a hospital drama on TV."',
  'Settled during visit. Weight stable. Sleep improved per diary.',
  'BPSD largely routine-responsive; TV trigger identified. Non-drug approach holding.',
  'Avoid evening TV dramas. Continue diary. Reassess in a week; still no antipsychotic indication.',
  '2026-08-19 14:15+09'),
 -- P-014 ALS: grip を追う
 ('P-014','2026-08-05','Dr-C','regular',
  '"Buttons are getting hard. Walking still fine."',
  'Grip strength R 18kg / L 22kg (dynamometer). Fasciculations both forearms. Gait steady. Bloods drawn.',
  'ALS limb-onset — right grip declining, ambulation preserved.',
  'OT referral for button aids. Riluzole continues. Recheck grip both hands next visit.',
  '2026-08-05 15:30+09'),
 ('P-014','2026-08-12','Dr-C','regular',
  '"Dropped a cup twice this week."',
  'Grip R 16kg / L 21kg — right down 2kg in a week. Speech and swallow unaffected. Bloods drawn.',
  'Right grip decline continuing at ~2kg/week. Function compensating with left.',
  'OT visit booked. Discuss adaptive cutlery. Monitor for bulbar signs — none yet.',
  '2026-08-12 15:25+09'),
 ('P-014','2026-08-19','Dr-C','regular',
  '"The thick-handled spoon works."',
  'Grip R 15kg / L 21kg. Weight stable. Respiratory rate normal, speech clear. Bloods drawn.',
  'Grip decline slowing (1kg this week). No bulbar or respiratory involvement.',
  'Continue riluzole and OT plan. Grip chart updated — bring to neurology clinic visit.',
  '2026-08-19 15:35+09'),
 -- P-015 cirrhosis: ascites を追う
 ('P-015','2026-08-06','Dr-B','regular',
  '"Trousers tight again. No confusion, sleeping fine."',
  'Abdominal girth 96cm. Shifting dullness present. No asterixis. Ankles +1.',
  'Recurrent ascites re-accumulating on current diuretics. No encephalopathy.',
  'Weigh daily. Salt talk repeated. Review girth next visit — escalate diuretics if over 97cm.',
  '2026-08-06 10:50+09'),
 ('P-015','2026-08-13','Dr-B','regular',
  '"Heavier this week."',
  'Girth 98cm (+2). Weight +1.4kg. No fever, no abdominal pain. Anticoagulant week supplied.',
  'Ascites progressing — past the escalation line agreed last week.',
  'Furosemide dose up per hepatology protocol. Girth and weight daily. Call if confusion or fever — SBP risk explained to neighbour who checks in.',
  '2026-08-13 10:45+09'),
 ('P-015','2026-08-20','Dr-B','regular',
  '"Lighter. Trousers fit."',
  'Girth 95cm (-3). Weight -1.8kg. Electrolytes stable on this week''s draw at clinic. No cramps.',
  'Ascites responding to the increased diuretic. No overshoot signs.',
  'Hold new dose one more week, then reassess for step-down. Continue daily girth log.',
  '2026-08-20 10:55+09'),
 -- P-016 pressure ulcer: wound を追う
 ('P-016','2026-08-06','Dr-C','regular',
  'Son: "dressing changes going okay, he winces at turns."',
  'Sacral wound 4.2 x 3.1cm, stage III, red granulating base, no odour, no undermining. Dressing renewed, injection for pain given before care.',
  'Stage III sacral pressure ulcer — clean wound bed, healing conditions present.',
  'Two-hourly turns chart on the wall. Protein supplement continues. Photograph wound weekly.',
  '2026-08-06 16:20+09'),
 ('P-016','2026-08-13','Dr-C','regular',
  'Son: "turning chart is working, less wincing."',
  'Wound 3.8 x 2.9cm — smaller. Granulation healthy, edges advancing. Dressing renewed.',
  'Wound contracting week on week. Nutrition and off-loading adequate.',
  'Same dressing protocol. Keep photos. Praise the turning routine — it shows.',
  '2026-08-13 16:10+09'),
 ('P-016','2026-08-20','Dr-C','regular',
  'Son: "looks smaller to us too."',
  'Wound 3.4 x 2.6cm. Base fully granulating, early epithelial edge. No slough.',
  'Steady healing trajectory on the wound measurements — stage III improving.',
  'Continue protocol unchanged. Anticipate dressing simplification in 2 weeks if trend holds.',
  '2026-08-20 16:15+09'),
 -- P-017 PEG: PEG site / feeds を追う
 ('P-017','2026-08-07','Dr-C','regular',
  'Spouse: "feeds going in fine, a little redness at the button."',
  'PEG site mild erythema 5mm rim, no discharge, no granuloma. Weight 48.2kg. Feed tolerance good, no reflux. Flush line renewed.',
  'PEG feeding established; minor site irritation only. Malnutrition slowly correcting.',
  'Barrier cream at PEG site. Same feed rate. Weigh weekly — target +0.2kg/week.',
  '2026-08-07 09:40+09'),
 ('P-017','2026-08-14','Dr-C','regular',
  'Spouse: "redness looks better."',
  'PEG site clean, erythema resolved. Weight 48.5kg (+0.3). No aspiration signs.',
  'PEG site settled. Weight trend on target.',
  'Continue regimen. Review feed formula with dietitian call this week.',
  '2026-08-14 09:35+09'),
 ('P-017','2026-08-21','Dr-C','regular',
  '"He seems brighter," spouse says. No coughing with feeds.',
  'PEG site healthy. Weight 48.9kg (+0.4). Mid-arm circumference up 0.5cm this month.',
  'Nutrition recovering on PEG feeding — two consecutive weeks of gain.',
  'Same plan. Recheck albumin at next clinic bloods. Celebrate the trend with the family.',
  '2026-08-21 09:45+09'),
 -- P-018 LBD: hallucination を追う
 ('P-018','2026-08-08','Dr-B','regular',
  'Staff: "good days and bad days — yesterday he chatted, today he is far away."',
  'Fluctuating attention during visit. No parkinsonian rigidity change. Eating with prompting.',
  'Lewy body dementia, marked fluctuation. No hallucination reported this week.',
  'Staff to log alertness twice daily and note any hallucination episode. Avoid new sedatives.',
  '2026-08-08 10:30+09'),
 ('P-018','2026-08-15','Dr-B','regular',
  'Staff: "he described small figures in the room on Tuesday evening — calm about them."',
  'Alert today. Recounts the visual hallucination without distress. No threat content.',
  'First clear visual hallucination episode this month — classic for LBD, non-distressing.',
  'No antipsychotic (LBD sensitivity — noted in red on the facility sheet). Evening lighting increased. Log any further hallucination with time of day.',
  '2026-08-15 10:25+09'),
 ('P-018','2026-08-22','Dr-B','regular',
  'Staff: "one more hallucination Thursday dusk, again calm. Lighting change seems to help."',
  'Attention better today. Gait unchanged. Appetite fair.',
  'Hallucination episodes clustering at dusk, non-distressing, frequency stable.',
  'Keep dusk lighting protocol. Continue log. Review donepezil dose next month if episodes increase.',
  '2026-08-22 10:35+09'),
 -- P-019 multi-infarct: suction を追う
 ('P-019','2026-08-08','Dr-B','regular',
  'Staff: "needs suction after most meals now."',
  'Chest clear between meals. Secretions moderate; suction performed after lunch during the visit. Injection given per plan. Extended visit for airway care teaching.',
  'Dysphagia with post-prandial secretion load — suction dependence increasing.',
  'Thickened fluids trial. Staff suction technique reviewed at bedside. ST review requested.',
  '2026-08-08 11:40+09'),
 ('P-019','2026-08-15','Dr-B','regular',
  'Staff: "suction needed after lunch daily this week."',
  'Low-grade rhonchi clearing with suction. Afebrile. Hydration borderline. Extended visit again for positioning work.',
  'Suction needs up — aspiration risk rising. No infection yet.',
  'Head-of-bed 45 degrees after meals for 60 min. Suction log per shift. Chest sounds check at every visit.',
  '2026-08-15 11:35+09'),
 ('P-019','2026-08-22','Dr-B','regular',
  'Staff: "positioning helps — suction once most days now."',
  'Chest clear today. Suction log shows reduction from 3/day to 1/day. Afebrile all week.',
  'Secretion management improved with positioning; suction trend down.',
  'Continue positioning protocol and log. ST assessment booked. Escalate if fever or suction rises again.',
  '2026-08-22 11:45+09'),
 -- P-020 palliative: NRS を追う
 ('P-020','2026-08-09','Dr-C','regular',
  'Wife: "pain about NRS 4 most of the day, 6 by late afternoon."',
  'Alert, comfortable at rest. Oxycodone SR taken reliably; one day''s supply dispensed and infusion for hydration support given.',
  'Baseline pain NRS 4 with predictable late-afternoon breakthrough to 6.',
  'Rescue dose timed 15:30 pre-emptively. Pain diary with NRS three times daily. Bowel regimen continues.',
  '2026-08-09 13:20+09'),
 ('P-020','2026-08-16','Dr-C','regular',
  'Wife: "the 15:30 rescue works — most days NRS stays at 4."',
  'Diary: NRS 3-4 daytime, one evening spike to 6 after visitors. Appetite small, mood good.',
  'Pre-emptive rescue effective; pain NRS controlled at target most days.',
  'Continue schedule. Discuss visitor pacing. Anticipatory meds checklist reviewed with wife.',
  '2026-08-16 13:15+09'),
 ('P-020','2026-08-23','Dr-C','regular',
  '"Good week," both say. NRS diary consistently 3-4.',
  'Comfortable. Diary median NRS 3. No new sites of pain. Bowels regular on regimen.',
  'Stable palliative phase — pain NRS at best control this month.',
  'No changes. Next review Sunday. Weekend contact card re-confirmed on the fridge.',
  '2026-08-23 13:25+09'),
 -- P-022 post-PCI: BP を追う(単発)
 ('P-022','2026-08-14','Dr-B','regular',
  '"No chest pain since the stent. I walk to the corner shop daily."',
  'BP 128/76, HR 58 reg. No angina on the walk test to the genkan and back. Hydration infusion given per post-PCI protocol.',
  'Post-PCI course uncomplicated; BP at target on current regimen.',
  'Continue DAPT and statin. Home BP log twice weekly. Next scheduled review in 4 weeks.',
  '2026-08-14 14:50+09')
) AS n(patient, day, clinician, kind, s, o, a, p, at)
JOIN visits v
  ON v.patient = n.patient AND v.visit_date = n.day::date AND v.kind = n.kind;

-- 検算: 注記32本(P-011=4, P-012..P-020=3ずつ, P-022=1)が全部訪問に紐付いたか
-- (紐付かない注記は算定に見えない)
DO $$
DECLARE n_notes INT; n_visits INT;
BEGIN
  SELECT count(*) INTO n_notes FROM clinical_notes
   WHERE patient >= 'P-011' AND patient <= 'P-022' AND visit_id IS NOT NULL;
  SELECT count(*) INTO n_visits FROM visits
   WHERE patient >= 'P-011' AND patient <= 'P-022' AND status = 'done';
  IF n_notes <> 32 OR n_visits <> 32 THEN
    RAISE EXCEPTION 'expand seed mismatch: % signed notes, % done visits (want 32/32)', n_notes, n_visits;
  END IF;
END $$;

COMMIT;
