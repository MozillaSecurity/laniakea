#!/usr/bin/env bash

# Bash Utilities
function retry {
	for i in {1..5}; do $@ && break || sleep 1; done
}
