---
layout: post
title:  "Google CTF 2022 - Segfault Labyrinth"
categories: writeup
tags: google-ctf reversing reverse-engineering writeup
toc: true
---

## Summary Information

- Name: Segfault Labyrinth

- Author: Carl Svensson

- Category: Reversing

- Description: Be careful! One wrong turn and the whole thing comes crashing
  down

- Host: segfault-labyrinth.2022.ctfcompetition.com 

- Port: 1337

## Overview

The challenge provides a binary that is a stripped ELF 64-bit (why so stripped).
Checking the security settings using `checksec`, it returns the following:

{% include gctf-2022-misc-segfault-checksec.html %}

First interesting thing is that the binary has writable segments, what it will
be useful later.

## Final Considerations
...
