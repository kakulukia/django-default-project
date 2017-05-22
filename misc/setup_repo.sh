#!/usr/bin/env bash
flake8 --install-hook=git
git config flake8.strict true
