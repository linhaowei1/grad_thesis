import openai
import time
import multiprocessing

openai.api_key = None

prompts = []

# Define a function to submit a prompt to the OpenAI API
def submit_prompt(prompt):
    while True:
        try:
            # Submit the prompt to the OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an excellent theorem prover. Each proof line contains three parts: (1) 'premise' or 'goal'; (2) the rule used; (3) transformation\nThe transformation takes the form of A => B.\nIf the rule is substitution, write what premise used.\nIf the transformation is equivalence, use 'rewrite', otherwise use 'imply'.\nFor example,\npremise [x=y]: x + y >= 0 => y + y >= 0\npremise [x=0]: y + 2 * x >= 0 => y + 2 * 0 >= 0\npremise [rewrite]: 4*y >= 0 => 2*y >= 0\npremise [imply]: x >= 0, y >= 0 => x + y >= 0\npremise [imply]: x >= 0, y >= 0, y+z >= 0 => x * y ' (y+z)e'= 0\'goal'[rewrite]: x + y + y >= 0 => x + 2*y >= 0"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
            # Return the generated text
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error: {e}")

for idx in range(100):

    with open('./problems/problem{}.txt'.format(str(idx)), 'r') as f:
        prompt = f.read()
    
    prompts.append(prompt)

# Create a pool of worker processes to submit the prompts in parallel
with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
    # Submit the prompts to the OpenAI API in batches of 10
    batch_size = 10
    for i in range(0, len(prompts), batch_size):
        batch_prompts = prompts[i:i+batch_size]
        batch_results = pool.map(submit_prompt, batch_prompts)
        
        # Print the results for each prompt in the batch
        for j, result in enumerate(batch_results):
            prompt_index = i + j
            with open('./solutions/solution{}.txt'.format(str(prompt_index)), 'a') as f:
                f.write('\n')
                f.write(result)
            print(f"{prompt_index} ok.")
        
        # Wait for 1 second to avoid exceeding the API rate limit
        time.sleep(1)