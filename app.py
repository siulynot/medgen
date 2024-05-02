import logging
from flask import Flask, render_template, request, send_file, url_for
import openai
from openai import OpenAI
import markdown
from transformers import AutoTokenizer, AutoModel
from decouple import config
import subprocess
import os
import json
import io
import shutil


app = Flask(__name__)

condition_prompt = r"""
Generate a structured blog post in Spanish about CONDITION, formatted for LaTeX. This post is designed for patient education, particularly aimed at elderly patients, ensuring clarity and accessibility. Each section should have a bold title and adhere to the following structure:

1. **Title** [Centered, Bold]: "\textbf{{\begin{{center}}CONDITION\end{{center}}}}" — Replace "CONDITION" with the actual medical condition name, ensuring the title is bold and centered.

2. **Introduction**: Provide a brief overview explaining the relevance of CONDITION and why understanding it is crucial for affected individuals. Use clear and straightforward language to aid comprehension.

3. **Definition**: Clearly define what CONDITION is, using layman's terms. Ensure the definition is accessible, avoiding complex medical jargon that could confuse elderly readers.

4. **Causes**: List and describe 3-4 key factors or contributors that lead to CONDITION, ensuring clarity in how these factors are linked to the condition. Present the causes in a manner that is easy to understand.

5. **Risk Factors**: Identify demographic groups or lifestyles that increase the risk of developing CONDITION, emphasizing common risk profiles. Highlight these in bullet points for better readability.

6. **Symptoms**: Create a bullet list of the primary and secondary symptoms associated with CONDITION, making it easy for readers to identify them. Use "\begin{{itemize}} \item Symptom \end{{itemize}}" for listing the symptoms.

7. **Treatments**: Discuss the standard medical treatments available for CONDITION, and include any lifestyle changes or home remedies that can help manage the symptoms. Clearly differentiate between medical treatments and home remedies.

8. **Prevention**: Offer practical advice on preventive measures that can be taken to avoid the development of CONDITION. Include tips that are feasible for elderly individuals.

9. **Conclusion**: Emphasize the importance of consulting with a healthcare provider for a personalized diagnosis and treatment plan. Encourage proactive health management.

Ensure the text uses double spacing for readability, which can be achieved in LaTeX by setting "\renewcommand{{\baselinestretch}}{{2.0}}". The document should be concise, aiming to fit within two standard pages of text. Exclude any LaTeX document setup commands like "\documentclass" and "\usepackage" from the output as these are assumed to be handled by your existing LaTeX setup.
"""

medication_prompt = r"""
Generate a structured blog post in Spanish about MEDICATION, formatted for LaTeX. This post is designed for patient education and should be clear and easy to understand for elderly patients. Each section should have a bold title, formatted as follows:

1. **Title** [Centered, Bold]: "\textbf{{\begin{{center}}Información esencial sobre MEDICATION\end{{center}}}}" — Replace "MEDICATION" with the actual name of the medication, ensuring the title is bold and centered.

2. **What It Is**: Begin with a brief introduction to MEDICATION, explaining what it is used for in a general medical context. Start this section with clear, straightforward language to aid understanding.

3. **Uses**: Detail the primary and secondary uses of MEDICATION, focusing on why and how it is typically prescribed. Explain the applications in simple terms to ensure it is comprehensible for non-specialists.

4. **Side Effects**: List the common and less common side effects, ensuring to differentiate between minor inconveniences and serious health risks. Use bullet points for clarity, starting with "\begin{{itemize}} \item Side effect \end{{itemize}}".

5. **Precautions**: Discuss any necessary precautions that patients should be aware of before starting MEDICATION. This includes any dietary restrictions, interactions with other medications, or activities to avoid. Make sure to list these precautions in an easy-to-understand manner.

6. **Interactions**: Elaborate on how MEDICATION interacts with other drugs, foods, or medical conditions that could alter its effectiveness or exacerbate side effects. Provide examples to illustrate these interactions clearly.

7. **Conclusion**: Summarize the key points and emphasize the importance of following medical advice and consulting with a healthcare provider for personalized information. Highlight the need for professional guidance before making any decisions related to MEDICATION usage.

Ensure the text uses double spacing for readability, which can be achieved in LaTeX by setting "\renewcommand{{\baselinestretch}}{{2.0}}". The document should be concise, aiming to fit within two standard pages of text. Exclude any LaTeX document setup commands like "\documentclass" and "\usepackage" from the output as these are assumed to be handled by your existing LaTeX setup.
"""

def generate_care_plan(client, prompt, condition):
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {
                    "role": "system",
                    "content": "You are a home health Expert in Medical Educations. You know to do medical educations for conditions and medications in latex format. You know Spanish from Puerto Rico. You only provide educations that have nothing more, no expressions, references or comments of your own. You will not comment things like: Absolutely, here's a detailed blog post about... "
                },
                {"role": "assistant", "content": f"The patient information is as follows:\nCONDITION"},
                {"role": "user", "content": f"Based on this information, {prompt}"}
            ],
        )
        response = completion.choices[0].message.content.strip()
        return response.strip()
    except Exception as e:
        print("Error during OpenAI API call:", e)
        return ""


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def generate_text():
    prompt_type = request.form['prompt']
    condition = request.form['condition']
    
    # Create the prompt
    if prompt_type == 'condition':
        full_prompt = condition_prompt.replace('CONDITION', condition)
    elif prompt_type == 'medication':
        full_prompt = medication_prompt.replace('MEDICATION', condition)

    print(full_prompt)
    
    # Initialize the OpenAI client
    client = OpenAI(api_key=config('API_KEY'))

    # Generate the care plan
    care_plan = generate_care_plan(client, full_prompt, condition)
    print(care_plan)

    with open("output.txt", "w") as f:
        f.write(care_plan)

    # Compile the LaTeX document
    compile_tex("texfile.tex")

     # Set the path for the rendered PDF
    shutil.copy('texfile.pdf', 'static/texfile.pdf')
    pdf_url = url_for("static", filename="texfile.pdf")

    return render_template('index.html', pdf_url=pdf_url)


    #return render_template('index.html', 'texfile.pdf')



def compile_tex(tex_file):
    # Assume LaTeX compilation logic
    print("TeX file compiled successfully.")

def compile_tex(tex_file):
    process = subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_file])
    if process.returncode == 0:
        print("TeX file compiled successfully.")
    else:
        print("Error compiling TeX file.")

@app.route('/download')
def download():
    return send_file('texfile.pdf', as_attachment=True)


if __name__ == '__main__':
    print("Starting Flask development server...")
    app.run(debug=False)

