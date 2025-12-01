# Critic / Creator Agents

This repository is my personal attempt at creating a multi-agent workflow for creating and refining an ad copy.


## Overview

Two agents, the **Creator** and the **Editor** work together to iteratively produce an ad copy for a specified product and target audience.

The **Creator** writes the ad copy given the product and target audience.

The **Editor** checks the ad copy against a strict set of rules and determines its adherence.

If the copy needs improvement, the **Editor** gives constructive feedback to the **Creator**, which then produces a refined version to be sent back to the **Editor**.

Once the **Editor** determines that the copy fulfills its requirements, it is output in the console.


## Installation

Simply create a new virtual environment and use `pip` to install dependencies from `requirements.txt`.

The script uses Google Gemini so you must create a file at the project root containing your API key in this format:

```
GOOGLE_API_KEY=[your API key here]
```
