# Critic / Creator Agents

This repository is my personal attempt at creating a multi-agent workflow for 
creating and refining an ad copy.

I chose this task because I am interested in learning more about creating 
multi-agent workflows using LangGraph.


## Overview

Two agents, the **Creator** and the **Editor**, work together to iteratively 
produce an ad copy for a specified product and target audience.

The **Creator** writes the ad copy given the product and target audience.

The **Editor** checks the ad copy against a strict set of rules and determines 
its adherence.

If the copy needs improvement, the **Editor** gives constructive feedback to the
 **Creator**, which then produces a refined version to be sent back to the 
 **Editor**.

Once the **Editor** determines that the copy fulfills its requirements (or the 
maximum number of retries is reached), it is output in the console in a strict 
JSON format.


## Usage

1. Create and activate a new virtual environment and use `pip` to install dependencies 
from `requirements.txt`.

2. The script uses Google Gemini so you must create a file named `.env` at the project
root containing your API key in this format:

```
GOOGLE_API_KEY=[your API key here]
```

3. Run the script with the following command:

```bash
python main.py --product [product name] --audience [target audience] --verbose --max-retries [number of retries]
```

> Choosing not to specify the product or audience will result in the script running with placeholder values.


## Challenges

While creating the script I found that the agents entered a loop of rejections 
which resulted in only failures due to the max retries being reached.

This was solved by adding the rejection history to the **Creator**'s prompt,
which allowed it to avoid repeatedly making the same mistakes.


## AI Usage

The script was written using Google's new 'Antigravity' AI-assisted IDE, similar
 to Cursor.
Gemini 3 Pro (High) was selected as the Agent and is largely responsible for 
writing the code according to my specifications.

The first prompt was:

```
I'd like to create a 2-agent workflow for refining an ad copy. 

The 2 agents are:
> The Creator: writes up the ad copy
> The Editor: reviews the copy against a set of strict rules 

Given a product name and target audience as input, the Creator proposes a caption to be evaluated by the Critic.
If the Critic deems the copy unsuitable for the ruleset, it generates feedback and the Creator tries again based on this feedback.
Once the caption has been approved by the Critic, the loop ends and the script should output the final approved result.

Please create this system using only the Python standard library and LangChain/LangGraph. 

The system will use the Google Gemini API to generate responses from the agents, storing the API key in a .env file.
```

Further prompts were used to refine the script, introducing argument parsing 
for each optional parameter and keeping track of the feedback history.
