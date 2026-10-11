DELETE FROM warehouse_department;
INSERT INTO warehouse_department
SELECT department, COUNT(*), ROUND(SUM(fte), 2),
 SUM(employment_type='employee'), SUM(employment_type='contractor'), SUM(employment_type='intern')
FROM workforce GROUP BY department;
DELETE FROM warehouse_country;
INSERT INTO warehouse_country SELECT country, COUNT(*), ROUND(SUM(fte), 2) FROM workforce GROUP BY country;
