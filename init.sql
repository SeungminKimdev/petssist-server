-- .env파일에 맞게 수정 필요

-- 사용자 생성
-- CREATE USER DB_USER WITH PASSWORD DB_PASSWORD;
CREATE USER pelikan WITH PASSWORD '1234';

-- 새 데이터베이스 생성
-- CREATE DATABASE DB_NAME;
CREATE DATABASE test;

-- 생성한 사용자에게 새 데이터베이스의 모든 권한 부여
ALTER ROLE pelikan SUPERUSER;
