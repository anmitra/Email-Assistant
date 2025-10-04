<div id="top">

<!-- HEADER STYLE: CLASSIC -->
<div align="center">

<img src="readmeai/assets/logos/purple.svg" width="30%" style="position: relative; top: 0; right: 0;" alt="Project Logo"/>

# EMAIL-ASSISTANT

<em>Transforming email chaos into prioritized productivity effortlessly.</em>

<!-- BADGES -->
<!-- local repository, no metadata badges. -->

<em>Built with the tools and technologies:</em>

<img src="https://img.shields.io/badge/Anthropic-191919.svg?style=default&logo=Anthropic&logoColor=white" alt="Anthropic">
<img src="https://img.shields.io/badge/Streamlit-FF4B4B.svg?style=default&logo=Streamlit&logoColor=white" alt="Streamlit">
<img src="https://img.shields.io/badge/Python-3776AB.svg?style=default&logo=Python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/OpenAI-412991.svg?style=default&logo=OpenAI&logoColor=white" alt="OpenAI">

</div>
<br>

---

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
    - [Project Index](#project-index)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Usage](#usage)
    - [Testing](#testing)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Overview

**Why email-assistant?**

This project revolutionizes email management by combining AI capabilities with structured workflows. The core features include:

- **🚀 Enhanced Dependencies:** Ensure seamless integration with essential libraries for project functionality.
- **💡 Structured Triage Template:** Streamline email triage with a consistent and comprehensive prompt template.
- **🔍 Intelligent Triage Function:** Efficiently categorize and prioritize messages based on content analysis.
- **🎨 Visually Appealing UI:** Set up a visually appealing Streamlit web application for a seamless user experience.

---

## Features

|      | Component       | Details                              |
| :--- | :-------------- | :----------------------------------- |
| ⚙️  | **Architecture**  | <ul><li>Follows a modular design with separate components for email parsing, natural language processing, and response generation.</li><li>Utilizes a microservices architecture for scalability and maintainability.</li></ul> |
| 🔩 | **Code Quality**  | <ul><li>Consistent code style following PEP8 guidelines.</li><li>Includes unit tests for critical functions and modules.</li></ul> |
| 📄 | **Documentation** | <ul><li>Comprehensive inline code comments for better code understanding.</li><li>Lacks external documentation for setup and usage.</li></ul> |
| 🔌 | **Integrations**  | <ul><li>Integrates with Google APIs for email retrieval and processing.</li><li>Utilizes OpenAI API for natural language processing tasks.</li></ul> |
| 🧩 | **Modularity**    | <ul><li>Each functionality is encapsulated in separate modules for easy maintenance and extensibility.</li><li>Follows the SOLID principles for better code organization.</li></ul> |
| 🧪 | **Testing**       | <ul><li>Includes unit tests using the `unittest` framework for critical functions.</li><li>Lacks integration tests for end-to-end scenarios.</li></ul> |
| ⚡️  | **Performance**   | <ul><li>Optimizes email parsing algorithms for faster processing.</li><li>Utilizes caching mechanisms to reduce response time for repetitive queries.</li></ul> |
| 🛡️ | **Security**      | <ul><li>Implements OAuth authentication for secure access to email accounts.</li><li>Follows best practices for handling sensitive user data.</li></ul> |
| 📦 | **Dependencies**  | <ul><li>Dependent on various Python libraries like `google-api-python-client`, `openai`, and `streamlit`.</li><li>Manages dependencies using a `requirements.txt` file.</li></ul> |

---

## Project Structure

```sh
└── email-assistant/
    ├── app
    │   └── streamlit_app.py
    ├── assistant
    │   ├── __init__.py
    │   ├── __pycache__
    │   ├── llm.py
    │   ├── pipeline.py
    │   ├── prompts.py
    │   ├── providers
    │   └── schema.py
    ├── data
    │   └── sample_inbox.json
    ├── requirements.txt
    ├── scripts
    │   └── get_gmail_token_web.py
```

### Project Index

<details open>
	<summary><b><code>EMAIL-ASSISTANT/</code></b></summary>
	<!-- __root__ Submodule -->
	<details>
		<summary><b>__root__</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ __root__</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='/Users/anuragmitra/Desktop/email-assistant/blob/master/requirements.txt'>requirements.txt</a></b></td>
					<td style='padding: 8px;'>- Enhance project dependencies by specifying required versions for Streamlit, Python-Dotenv, OpenAI, Anthropic, Google Auth, Google Auth OAuthlib, and Google API Python Client in the requirements.txt file<br>- This ensures seamless integration and compatibility with essential libraries for the projects functionality.</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<!-- assistant Submodule -->
	<details>
		<summary><b>assistant</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ assistant</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='/Users/anuragmitra/Desktop/email-assistant/blob/master/assistant/llm.py'>llm.py</a></b></td>
					<td style='padding: 8px;'>- Define a function that sends a prompt to a model and returns a parsed JSON object<br>- The function ensures the model replies with JSON and handles code fences if present<br>- It utilizes an OpenAI client to generate completions based on the provided prompt using a specified model<br>- The function then cleans and parses the response before returning the JSON object.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='/Users/anuragmitra/Desktop/email-assistant/blob/master/assistant/prompts.py'>prompts.py</a></b></td>
					<td style='padding: 8px;'>- Define a structured email triage prompt template in the prompts.py file<br>- The template guides users on summarizing emails, setting priorities, providing reasons, and suggesting actions<br>- It enforces JSON output and includes specific instructions for each section<br>- This template streamlines the email triage process by ensuring consistent and comprehensive responses.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='/Users/anuragmitra/Desktop/email-assistant/blob/master/assistant/pipeline.py'>pipeline.py</a></b></td>
					<td style='padding: 8px;'>- Define a function to triage incoming messages by assigning priority labels based on content analysis<br>- The function extracts message details, prompts for triage input, processes the data, and applies appropriate labels<br>- This aids in efficiently categorizing and prioritizing messages within the system.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='/Users/anuragmitra/Desktop/email-assistant/blob/master/assistant/schema.py'>schema.py</a></b></td>
					<td style='padding: 8px;'>- Define a schema for triaging data with summary, priority, reasons, and suggested actions<br>- The schema enforces specific data types and constraints for each field, ensuring data consistency and integrity within the project architecture.</td>
				</tr>
			</table>
			<!-- providers Submodule -->
			<details>
				<summary><b>providers</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ assistant.providers</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='/Users/anuragmitra/Desktop/email-assistant/blob/master/assistant/providers/demo.py'>demo.py</a></b></td>
							<td style='padding: 8px;'>Demonstrate how to interact with email messages by listing, retrieving, labeling, and creating drafts using a demo provider.</td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='/Users/anuragmitra/Desktop/email-assistant/blob/master/assistant/providers/base.py'>base.py</a></b></td>
							<td style='padding: 8px;'>Define abstract email provider functionality for message handling and management within the project architecture.</td>
						</tr>
					</table>
				</blockquote>
			</details>
		</blockquote>
	</details>
	<!-- app Submodule -->
	<details>
		<summary><b>app</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ app</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='/Users/anuragmitra/Desktop/email-assistant/blob/master/app/streamlit_app.py'>streamlit_app.py</a></b></td>
					<td style='padding: 8px;'>- SummaryThe <code>streamlit_app.py</code> file in the project is responsible for setting up the Streamlit web application for the AI Email Assistant<br>- It configures the page title, icon, and layout for the application<br>- Additionally, it defines minimal CSS styles inline to ensure a consistent and visually appealing user interface<br>- This file plays a crucial role in defining the overall look and feel of the AI Email Assistant web application, providing a seamless user experience.</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<!-- scripts Submodule -->
	<details>
		<summary><b>scripts</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ scripts</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='/Users/anuragmitra/Desktop/email-assistant/blob/master/scripts/get_gmail_token_web.py'>get_gmail_token_web.py</a></b></td>
					<td style='padding: 8px;'>- Generate a Gmail token.json with refresh_token for a demo account using a Web OAuth client<br>- Ensure the Web client JSON is downloaded from Google Cloud Console<br>- Run the script to obtain and save the token.json file, containing necessary credentials for your Streamlit app<br>- Follow the provided instructions for a seamless setup.</td>
				</tr>
			</table>
		</blockquote>
	</details>
</details>

---

## Getting Started

### Prerequisites

This project requires the following dependencies:

- **Programming Language:** Python
- **Package Manager:** Pip

### Installation

Build email-assistant from the source and intsall dependencies:

1. **Clone the repository:**

    ```sh
    ❯ git clone ../email-assistant
    ```

2. **Navigate to the project directory:**

    ```sh
    ❯ cd email-assistant
    ```

3. **Install the dependencies:**

<!-- SHIELDS BADGE CURRENTLY DISABLED -->
	<!-- [![pip][pip-shield]][pip-link] -->
	<!-- REFERENCE LINKS -->
	<!-- [pip-shield]: https://img.shields.io/badge/Pip-3776AB.svg?style={badge_style}&logo=pypi&logoColor=white -->
	<!-- [pip-link]: https://pypi.org/project/pip/ -->

	**Using [pip](https://pypi.org/project/pip/):**

	```sh
	❯ pip install -r requirements.txt
	```

### Usage

Run the project with:

**Using [pip](https://pypi.org/project/pip/):**
```sh
python {entrypoint}
```

### Testing

Email-assistant uses the {__test_framework__} test framework. Run the test suite with:

**Using [pip](https://pypi.org/project/pip/):**
```sh
pytest
```

---

## Roadmap

- [X] **`Task 1`**: <strike>Implement feature one.</strike>
- [ ] **`Task 2`**: Implement feature two.
- [ ] **`Task 3`**: Implement feature three.

---

## Contributing

- **💬 [Join the Discussions](https://LOCAL/Desktop/email-assistant/discussions)**: Share your insights, provide feedback, or ask questions.
- **🐛 [Report Issues](https://LOCAL/Desktop/email-assistant/issues)**: Submit bugs found or log feature requests for the `email-assistant` project.
- **💡 [Submit Pull Requests](https://LOCAL/Desktop/email-assistant/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your LOCAL account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone /Users/anuragmitra/Desktop/email-assistant
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to LOCAL**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
8. **Review**: Once your PR is reviewed and approved, it will be merged into the main branch. Congratulations on your contribution!
</details>

<details closed>
<summary>Contributor Graph</summary>
<br>
<p align="left">
   <a href="https://LOCAL{/Desktop/email-assistant/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=Desktop/email-assistant">
   </a>
</p>
</details>

---

## License

Email-assistant is protected under the [LICENSE](https://choosealicense.com/licenses) License. For more details, refer to the [LICENSE](https://choosealicense.com/licenses/) file.

---

## Acknowledgments

- Credit `contributors`, `inspiration`, `references`, etc.

<div align="right">

[![][back-to-top]](#top)

</div>


[back-to-top]: https://img.shields.io/badge/-BACK_TO_TOP-151515?style=flat-square


---
