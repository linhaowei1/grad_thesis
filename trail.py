import openai
openai.api_key = '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'

response = openai.ChatCompletion.create(
  model="gpt-4",
  messages=[
        {"role": "system", "content": "You are an excellent theorem prover."},
        {"role": "user", "content": "Suppose $((-b)+f)=a$, prove this inequality step by step: $1=((((0+0)+a)*(b*(-b)))*(\frac{1}{((((b+(-b))+((-b)+f))*b)*(-b))}))$. Write in LaTeX format."},
    ]
)
print(response)