-- Default fraud rules. Thresholds live in DB, not code.
INSERT INTO risk_rules (name, threshold, action) VALUES
    ('large_amount', 5000000, 'FLAG'),
    ('high_velocity', 10, 'HOLD');