#!/usr/bin/env -S just --justfile

set shell := ["bash", "-uc"]
set export
set dotenv-load

default:
  @just --choose --justfile {{justfile()}}

init:
  @echo "export JUST_UNSTABLE=1" >> ~/.bashrc

