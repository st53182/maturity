
ALTER TABLE employee 
ADD COLUMN IF NOT EXISTS avatar VARCHAR(50) DEFAULT 'default.png';

UPDATE employee 
SET avatar = 'default.png' 
WHERE avatar IS NULL;

SELECT 'Migration completed successfully. Avatar column added to employee table.' as status;
