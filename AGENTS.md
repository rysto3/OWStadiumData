# Agents Guide

## Repo Description

This repo stores data related to Overwatch's Stadium Mode that displays custom made builds for users to choose from.

## Important Files

builds-download/scrape-builds.py

This python script fetches data from the StadiumBuilds website and stores them in the directory builds-download/build_rounds_data as individual JSON files

builds.json

This file exists in the root of the directory and acts as an Index file for the data in the builds-download/build_rounds_data directory. It contains some data about the builds but not all of it. The index entry will have an ID that either will match a build in builds-download/build_rounds_data or the scrape-builds.py script should add it.

## Suggestions

Review several builds to get an idea of the data structure. You can find them in builds-download/build_rounds_data

