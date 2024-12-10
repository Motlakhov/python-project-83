--
-- PostgreSQL database dump
--

-- Dumped from database version 14.13 (Ubuntu 14.13-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.13 (Ubuntu 14.13-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--- Создаем таблицу только если ее не существует
CREATE TABLE IF NOT EXISTS public.urls (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создаем последовательность только если ее не существует
CREATE SEQUENCE IF NOT EXISTS public.urls_id_seq;

-- Устанавливаем последовательность для столбца id
ALTER SEQUENCE public.urls_id_seq OWNED BY public.urls.id;

-- Добавляем уникальный индекс на поле name
CREATE UNIQUE INDEX IF NOT EXISTS urls_name_key ON public.urls(name);


-- Таблица проверок
CREATE TABLE IF NOT EXISTS public.url_checks (
    id SERIAL PRIMARY KEY, 
    url_id bigint REFERENCES public.urls(id), 
    status_code bigint, 
    h1 VARCHAR(255), 
    title VARCHAR(255), 
    description VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

