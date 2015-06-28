#ExportSQLServer
==========================

ExportSQLServer is a plugin to export SQL Server DDL files from the MySQL Workbench software.
It is written in Python, so will work on versions of MySQL Workbench > 6.2.

I modified the script initially written by Thomas Henlich - http://www.henlich.de/  

##Version

Implemented and tested with MySQL Workbench 6.3.4

##Usage

 * From MySQL Workbench, go to "Scripting -> Install Plugin/Module…";
 * From the dialog box, select the ExportSQLiServer_grt.py script;
 * Restart MySQL Workbench;
 * To generate your SQLServer DDL file, open your model and go to "Tools -> Catalog -> Export SQL Server CREATE script";
 * Type a file name and hit save;
 * Enjoy your SQL Server DDL file;

##Generated file example
 
###MySQL file generated with MySQL Workbench
Tools -> Objects -> Copy SQL to Clipboard
... 
CREATE TABLE IF NOT EXISTS `sakila`.`film` (
  `film_id` SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '',
  `title` VARCHAR(255) NOT NULL COMMENT 'This is the title comment, and this was added just to show that comments are handled.',
  `description` TEXT NULL COMMENT '',
  `release_year` YEAR NULL COMMENT '',
  `language_id` TINYINT UNSIGNED NOT NULL COMMENT '',
  `original_language_id` TINYINT UNSIGNED NULL DEFAULT NULL COMMENT '',
  `rental_duration` TINYINT UNSIGNED NOT NULL DEFAULT 3 COMMENT '',
  `rental_rate` DECIMAL(4,2) NOT NULL DEFAULT 4.99 COMMENT '',
  `length` SMALLINT UNSIGNED NULL DEFAULT NULL COMMENT '',
  `replacement_cost` DECIMAL(5,2) NOT NULL DEFAULT 19.99 COMMENT '',
  `rating` ENUM('G','PG','PG-13','R','NC-17') NULL DEFAULT 'G' COMMENT '',
  `special_features` SET('Trailers','Commentaries','Deleted Scenes','Behind the Scenes') NULL COMMENT '',
  `last_update` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '',
  INDEX `idx_title` (`title` ASC)  COMMENT '',
  INDEX `idx_fk_language_id` (`language_id` ASC)  COMMENT '',
  INDEX `idx_fk_original_language_id` (`original_language_id` ASC)  COMMENT '',
  PRIMARY KEY (`film_id`)  COMMENT '',
  CONSTRAINT `fk_film_language`
    FOREIGN KEY (`language_id`)
    REFERENCES `sakila`.`language` (`language_id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_film_language_original`
    FOREIGN KEY (`original_language_id`)
    REFERENCES `sakila`.`language` (`language_id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8
COMMENT = 'This is the description of the table film.'
... 
 
###SQL Server DDL file generated with MySQL Workbench and the ExportSQLServer plugin

... 
-- Creator       : MySQL Workbench 6.3.4 /ExportSQLServer plugin 2015.06.28
-- Author        : Roland
-- Caption       : New Model
-- Project       : Name of the project
-- Changed       : 2015-06-28 22:33
-- Created       : Jan 09, 2008

-- Schema: sakila 
CREATE SCHEMA [sakila];

-- Snip

CREATE TABLE [sakila].[film](
--   This is the description of the table film.
 [film_id] INTEGER NOT NULL CHECK([film_id]>=0),  
 [title] VARCHAR( 255 ) NOT NULL, -- This is the title comment, and this was added just to show that comments are handled. 
 [description] TEXT NULL,  
 [release_year] YEAR NULL,  
 [language_id] INTEGER NOT NULL CHECK([language_id]>=0),  
 [original_language_id] INTEGER NULL CHECK([original_language_id]>=0) DEFAULT NULL,  
 [rental_duration] INTEGER NOT NULL CHECK([rental_duration]>=0) DEFAULT 3,  
 [rental_rate] DECIMAL NOT NULL DEFAULT 4.99,  
 [length] INTEGER NULL CHECK([length]>=0) DEFAULT NULL,  
 [replacement_cost] DECIMAL NOT NULL DEFAULT 19.99,  
 [rating] VARCHAR(MAX) NULL CHECK([rating] IN ('G','PG','PG-13','R','NC-17')) DEFAULT 'G',  
 [special_features] SET NULL,  
 [last_update] TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  
  CONSTRAINT [fk_film_language] 
  FOREIGN KEY([language_id])
    REFERENCES [language] ( [language_id] )
    ON DELETE RESTRICT
    ON UPDATE CASCADE,  
  CONSTRAINT [fk_film_language_original] 
  FOREIGN KEY([original_language_id])
    REFERENCES [language] ( [language_id] )
    ON DELETE RESTRICT
    ON UPDATE CASCADE
);

exec sys.sp_addextendedproperty @name=N'MS_Description', @value=N'This is the description of the table film.', @level0type=N'SCHEMA', @level0name=N'sakila', @level1type=N'TABLE',@level1name=N'film';

exec sys.sp_addextendedproperty @name=N'MS_Description', @value=N'This is the title comment, and this was added just to show that comments are handled.', @level0type=N'SCHEMA', @level0name=N'sakila', @level1type=N'TABLE',@level1name=N'film', @level2type=N'COLUMN', @level2name=N'title';
CREATE INDEX [idx_title] ON [sakila].[film] ([title]);
CREATE INDEX [idx_fk_language_id] ON [sakila].[film] ([language_id]);
CREATE INDEX [idx_fk_original_language_id] ON [sakila].[film] ([original_language_id]);

-- Snip
...