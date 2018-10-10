# Catalog

## Introduction
Project for Udacity Full Stack Web Developer Nanodegree. Built on Flask and PostgreSQL.

## Description
Catalog is a database of items grouped by restaurants. Users can perform CRUD operations on their own
items. Authentication is via Facebook and Google Login.

## Prerequisite
1. If you haven't already, [install pip](https://pip.pypa.io/en/stable/installing/).
2. Install the dependencies. `pip install -r requirements.txt`
3. setup your psql environment. Check [this](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-16-04) out

## Quickstart
1. Git clone the repository and cd into it.
2. Setup the database by running the following commands.
	```
	$psql
	#= \i database_setup.sql
	```
3. Run the app. `python project.py`

## Usage
* Login by clicking the 'Login' link in the upper right dropdown
* Once logged in, you will be able to perform CRUD through buttons in the upper right dropdown 
* To view the JSON output, add `JSON` at the end of your URL, example:
	```
	localhost:5000/restaurant/JSON
	```
