# 🤖 AI Test Automation Agent — Master Plan

> **Project Name:** AutoTestAI  
> **Goal:** An AI-powered agent that reads manual test cases (Excel/DOCX), analyzes frontend HTML + screenshots, and auto-generates production-ready automation code with frameworks and reports.

---

## 1. Vision & High-Level Architecture

```mermaid
graph TB
    subgraph INPUT["📥 Inputs"]
        A["Excel / DOCX<br/>Manual Test Cases"]
        B["HTML Source Code<br/>Frontend Pages"]
        C["Screenshots<br/>UI Images"]
    end

    subgraph AI_ENGINE["🧠 AI Engine (Core Brain)"]
        D["Document Parser<br/>Excel / DOCX Reader"]
        E["HTML Analyzer<br/>DOM Inspector"]
        F["Vision AI<br/>Screenshot Analyzer"]
        G["LLM Orchestrator<br/>GPT-4 / Gemini / Local"]
        D --> G
        E --> G
        F --> G
    end

    subgraph CODE_GEN["⚙️ Code Generator"]
        H["Template Engine"]
        I["Framework Builder<br/>POM / Config / Utils"]
        J["Test Script Generator"]
        K["Report Integration<br/>ExtentReports / Allure"]
        G --> H
        H --> I
        H --> J
        H --> K
    end

    subgraph OUTPUT["📤 Outputs"]
        L["Java + Selenium Project"]
        M["Java + Playwright Project"]
        N["Python + Selenium Project"]
        O["Python + Playwright Project"]
        P["JS/TS + Playwright Project"]
        Q["ExtentReports / Allure HTML"]
    end

    A --> D
    B --> E
    C --> F
    I --> L & M & N & O & P
    J --> L & M & N & O & P
    K --> Q

    subgraph UI["🖥️ Web Dashboard"]
        R["Upload Interface"]
        S["Configuration Panel"]
        T["Code Preview & Download"]
        U["Execution Monitor"]
    end

    INPUT --> UI
    OUTPUT --> UI
```

---

## 2. Core Features Breakdown

### 2.1 Input Processing Module

| Feature | Description | Tech |
|---|---|---|
| **Excel Parser** | Reads `.xlsx`/`.xls` files containing test case IDs, steps, expected results, test data | Apache POI (Java), `openpyxl` (Python) |
| **DOCX Parser** | Extracts structured test cases from Word documents including tables | Apache POI (Java), `python-docx` (Python) |
| **HTML Analyzer** | Parses HTML to extract element locators (id, class, name, data-testid, xpath, css) | Jsoup (Java), BeautifulSoup (Python) |
| **Screenshot Analyzer** | Uses Vision AI to identify UI elements, buttons, forms, flows from screenshots | GPT-4 Vision / Gemini Vision API |
| **Smart Mapper** | Maps test case steps → HTML elements → locators using AI reasoning | LLM + custom prompt chains |

### 2.2 AI Engine (Core Brain)

| Component | Purpose |
|---|---|
| **LLM Orchestrator** | Routes requests to configured AI provider (OpenAI, Gemini, Local LLM) |
| **Prompt Templates** | Pre-built, optimized prompts for test case parsing, locator extraction, code generation |
| **Context Builder** | Assembles rich context from parsed test cases + HTML + screenshots for AI |
| **Validation Agent** | AI-powered self-review of generated code for correctness, best practices |
| **Retry & Fallback** | Automatic retry with refined prompts on failure; fallback between AI providers |

### 2.3 Code Generation Engine

Generates **complete, runnable projects** — not just test scripts:

```
generated-project/
├── src/
│   ├── main/
│   │   └── java/com/autotest/
│   │       ├── pages/          # Page Object Model classes
│   │       ├── utils/          # WebDriver factory, config loader, helpers
│   │       ├── config/         # Configuration files
│   │       └── reports/        # ExtentReports setup
│   └── test/
│       └── java/com/autotest/
│           ├── tests/          # Generated test classes
│           ├── base/           # BaseTest with setup/teardown
│           └── data/           # Test data providers
├── testdata/                   # External test data files
├── reports/                    # Generated HTML reports
├── pom.xml / build.gradle      # Build configuration
├── testng.xml / pytest.ini     # Test runner config
└── README.md                   # Auto-generated documentation
```

### 2.4 Supported Output Combinations

| # | Language | Tool | Framework | Report |
|---|---|---|---|---|
| 1 | **Java** | Selenium | TestNG + POM | ExtentReports |
| 2 | **Java** | Selenium | JUnit 5 + POM | Allure |
| 3 | **Java** | Playwright | JUnit 5 + POM | ExtentReports |
| 4 | **Python** | Selenium | pytest + POM | ExtentReports / Allure |
| 5 | **Python** | Playwright | pytest + POM | Allure / HTML |
| 6 | **JavaScript** | Playwright | Mocha/Jest + POM | Playwright HTML Reporter |
| 7 | **TypeScript** | Playwright | Playwright Test + POM | Playwright HTML Reporter |

### 2.5 Web Dashboard (React + FastAPI)

```mermaid
graph LR
    subgraph Frontend["React Dashboard"]
        A["📤 Upload Zone<br/>Drag & Drop"]
        B["⚙️ Config Panel<br/>Language / Tool / Framework"]
        C["👁️ Preview Pane<br/>Generated Code Viewer"]
        D["📊 Execution Dashboard<br/>Run & Monitor Tests"]
        E["📥 Download Center<br/>Full Project ZIP"]
    end

    subgraph Backend["FastAPI Backend"]
        F["File Processing API"]
        G["AI Generation API"]
        H["Code Compilation API"]
        I["Test Execution API"]
        J["WebSocket for Live Logs"]
    end

    A --> F
    B --> G
    C --> G
    D --> I
    D --> J
    E --> H
```

---

## 3. Technology Stack

### 3.1 Backend (API Server)

| Layer | Technology | Why |
|---|---|---|
| **API Framework** | FastAPI (Python) | Async, fast, auto-docs, WebSocket support |
| **Task Queue** | Celery + Redis | Background code generation jobs |
| **File Storage** | Local FS + MinIO (S3-compat) | Store uploads and generated projects |
| **Database** | PostgreSQL | Project history, user settings, templates |
| **Cache** | Redis | LLM response caching, session cache |

### 3.2 Frontend (Web Dashboard)

| Layer | Technology | Why |
|---|---|---|
| **Framework** | React 18 + TypeScript | Component-based, ecosystem |
| **UI Library** | shadcn/ui + Tailwind | Modern, accessible, beautiful |
| **Code Editor** | Monaco Editor | VS Code-like code preview |
| **State Mgmt** | Zustand | Lightweight, powerful |
| **Real-time** | WebSocket | Live execution logs |

### 3.3 AI Layer

| Component | Technology |
|---|---|
| **Primary LLM** | OpenAI GPT-4o / GPT-4 Turbo |
| **Alternate LLM** | Google Gemini 1.5 Pro |
| **Local LLM** | Ollama (Llama 3, CodeLlama) |
| **Vision AI** | GPT-4 Vision / Gemini Vision |
| **LLM Framework** | LangChain (orchestration, prompts, memory) |
| **Vector Store** | ChromaDB (for template similarity search) |

### 3.4 Code Generation Layer

| Language | Dependencies |
|---|---|
| **Java** | Maven/Gradle, Selenium 4, Playwright Java, TestNG, JUnit 5, ExtentReports |
| **Python** | pip/poetry, selenium, playwright, pytest, allure-pytest |
| **JavaScript** | npm, @playwright/test, selenium-webdriver, mocha, jest |

---

## 4. Detailed Module Design

### 4.1 Module: Document Parser

```mermaid
flowchart TD
    A[Upload File] --> B{File Type?}
    B -->|.xlsx/.xls| C[Excel Parser]
    B -->|.docx| D[DOCX Parser]
    B -->|.csv| E[CSV Parser]
    
    C --> F[Extract Sheet Data]
    D --> G[Extract Tables & Paragraphs]
    E --> H[Parse Rows]
    
    F --> I[Normalize to Standard Schema]
    G --> I
    H --> I
    
    I --> J["Structured Test Cases JSON"]
    
    J --> K["[{<br/>  id: 'TC001',<br/>  title: 'Login Test',<br/>  preconditions: '...',<br/>  steps: [{action, element, data, expected}],<br/>  priority: 'High'<br/>}]"]
```

**Standard Test Case Schema:**
```json
{
  "test_case_id": "TC001",
  "title": "Verify user login with valid credentials",
  "module": "Authentication",
  "priority": "High",
  "preconditions": ["User must be registered", "Browser is open"],
  "steps": [
    {
      "step_number": 1,
      "action": "Navigate to login page",
      "test_data": "https://example.com/login",
      "element_description": "browser URL bar",
      "expected_result": "Login page is displayed"
    },
    {
      "step_number": 2,
      "action": "Enter username",
      "test_data": "testuser@example.com",
      "element_description": "Username input field",
      "expected_result": "Username is entered"
    },
    {
      "step_number": 3,
      "action": "Enter password",
      "test_data": "SecurePass123",
      "element_description": "Password input field",
      "expected_result": "Password is masked and entered"
    },
    {
      "step_number": 4,
      "action": "Click login button",
      "test_data": null,
      "element_description": "Login/Submit button",
      "expected_result": "User is redirected to dashboard"
    }
  ],
  "postconditions": ["User is logged in", "Dashboard is visible"]
}
```

### 4.2 Module: HTML Analyzer & Locator Engine

```mermaid
flowchart LR
    A["HTML Source Code"] --> B["DOM Parser<br/>(Jsoup / BeautifulSoup)"]
    B --> C["Element Catalog"]
    C --> D["Locator Strategy Engine"]
    
    D --> E["Priority-based Locators:"]
    E --> F["1. data-testid"]
    E --> G["2. id"]
    E --> H["3. name"]
    E --> I["4. CSS Selector"]
    E --> J["5. XPath"]
    
    D --> K["Element Metadata:<br/>tag, type, text, attributes,<br/>parent, siblings, visibility"]
```

**Locator Priority Strategy:**
1. `data-testid` / `data-test` → Most reliable, CI-safe
2. `id` → Unique, fast
3. `name` → Form elements
4. `CSS Selector` → Flexible, readable
5. `XPath` → Last resort, complex traversals

### 4.3 Module: Vision AI (Screenshot Analysis)

```mermaid
flowchart TD
    A["Screenshot Image"] --> B["Vision AI API<br/>(GPT-4V / Gemini Vision)"]
    B --> C["Identified UI Components"]
    C --> D["Buttons, Inputs, Links,<br/>Dropdowns, Modals, Tables"]
    
    C --> E["Spatial Mapping"]
    E --> F["Element Positions & Hierarchy"]
    
    C --> G["Flow Detection"]
    G --> H["User Journey Steps"]
    
    D & F & H --> I["Enriched Element Map"]
    I --> J["Cross-reference with<br/>HTML Locators & Test Steps"]
```

**Use Cases:**
- When HTML is unavailable, infer elements from screenshots alone
- Validate that HTML locators match visual elements
- Detect UI components that may not be obvious from HTML (dynamic/shadow DOM)
- Map test case descriptions to visual elements

### 4.4 Module: AI Code Generation Pipeline

```mermaid
flowchart TD
    A["Structured Test Cases"] --> D["Context Assembler"]
    B["Element Locator Map"] --> D
    C["User Config<br/>(Lang/Tool/Framework)"] --> D
    
    D --> E["Prompt Builder"]
    E --> F["LLM API Call"]
    
    F --> G["Raw Generated Code"]
    G --> H["Code Validator"]
    
    H -->|Valid| I["Code Formatter"]
    H -->|Invalid| J["Error Analyzer"]
    J --> K["Refined Prompt"]
    K --> F
    
    I --> L["Project Assembler"]
    L --> M["Complete Project<br/>(POM + Config + Tests + Reports)"]
```

**Prompt Engineering Strategy:**

| Prompt Type | Purpose |
|---|---|
| **System Prompt** | Define AI's role as senior SDET, enforce coding standards |
| **Test Case Prompt** | Convert parsed test case into executable test method |
| **Page Object Prompt** | Generate Page Object classes from locator maps |
| **Framework Prompt** | Generate BaseTest, utilities, config classes |
| **Report Prompt** | Integrate ExtentReports/Allure with proper annotations |
| **Review Prompt** | Self-review generated code for correctness |

### 4.5 Module: Report Integration

| Report Tool | Languages | Features |
|---|---|---|
| **ExtentReports** | Java, Python (via extentreports) | Rich HTML, screenshots on failure, tags, categories |
| **Allure** | Java, Python, JS | Interactive dashboard, trends, history |
| **Playwright HTML** | JS/TS | Built-in, trace viewer |
| **Custom HTML** | All | Lightweight fallback |

**Report Features Auto-Generated:**
- ✅ Test pass/fail/skip status
- ✅ Screenshots on failure (auto-captured)
- ✅ Step-by-step execution logs
- ✅ Execution duration metrics
- ✅ Environment/browser info
- ✅ Category & tag grouping

---

## 5. Project Structure

```
AutoTestAI/
├── 📂 backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI entry point
│   │   ├── config.py                    # App configuration
│   │   ├── models/                      # Pydantic models
│   │   │   ├── test_case.py
│   │   │   ├── project.py
│   │   │   └── generation_request.py
│   │   ├── api/                         # API routes
│   │   │   ├── upload.py                # File upload endpoints
│   │   │   ├── generate.py              # Code generation endpoints
│   │   │   ├── execute.py               # Test execution endpoints
│   │   │   └── projects.py              # Project management
│   │   ├── services/                    # Business logic
│   │   │   ├── parser/
│   │   │   │   ├── excel_parser.py
│   │   │   │   ├── docx_parser.py
│   │   │   │   └── html_analyzer.py
│   │   │   ├── ai/
│   │   │   │   ├── llm_orchestrator.py  # Multi-provider LLM router
│   │   │   │   ├── prompt_builder.py    # Prompt template engine
│   │   │   │   ├── vision_analyzer.py   # Screenshot analysis
│   │   │   │   └── code_validator.py    # Generated code validation
│   │   │   ├── generator/
│   │   │   │   ├── java_selenium.py     # Java + Selenium generator
│   │   │   │   ├── java_playwright.py   # Java + Playwright generator
│   │   │   │   ├── python_selenium.py   # Python + Selenium generator
│   │   │   │   ├── python_playwright.py # Python + Playwright generator
│   │   │   │   ├── js_playwright.py     # JS + Playwright generator
│   │   │   │   └── template_engine.py   # Jinja2 template renderer
│   │   │   └── executor/
│   │   │       ├── runner.py            # Test execution engine
│   │   │       └── report_collector.py  # Collect & serve reports
│   │   ├── templates/                   # Code templates (Jinja2)
│   │   │   ├── java/
│   │   │   │   ├── selenium/
│   │   │   │   │   ├── pom.xml.j2
│   │   │   │   │   ├── BaseTest.java.j2
│   │   │   │   │   ├── PageObject.java.j2
│   │   │   │   │   ├── TestClass.java.j2
│   │   │   │   │   └── ExtentConfig.java.j2
│   │   │   │   └── playwright/
│   │   │   │       └── ...
│   │   │   ├── python/
│   │   │   │   ├── selenium/
│   │   │   │   │   ├── conftest.py.j2
│   │   │   │   │   ├── base_page.py.j2
│   │   │   │   │   ├── page_object.py.j2
│   │   │   │   │   └── test_class.py.j2
│   │   │   │   └── playwright/
│   │   │   │       └── ...
│   │   │   └── javascript/
│   │   │       └── playwright/
│   │   │           └── ...
│   │   └── core/
│   │       ├── database.py              # DB connection
│   │       ├── storage.py               # File storage
│   │       └── websocket.py             # WebSocket manager
│   ├── tests/                           # Backend tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── 📂 frontend/                         # React Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── Upload/                  # File upload area
│   │   │   ├── Config/                  # Language/tool selector
│   │   │   ├── CodePreview/             # Monaco code viewer
│   │   │   ├── Execution/              # Test run dashboard
│   │   │   └── common/                  # Shared UI components
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Generator.tsx
│   │   │   ├── Projects.tsx
│   │   │   └── Settings.tsx
│   │   ├── services/                    # API client
│   │   ├── stores/                      # Zustand stores
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
│
├── 📂 prompts/                          # AI Prompt Library
│   ├── system_prompts/
│   ├── test_generation/
│   ├── page_object_generation/
│   └── review_prompts/
│
├── 📂 docs/                             # Documentation
│   ├── API.md
│   ├── SETUP.md
│   └── ARCHITECTURE.md
│
├── docker-compose.yml                   # Full stack orchestration
├── .env.example                         # Environment variables
└── README.md
```

---

## 6. Development Phases & Timeline

### Phase 1: Foundation (Weeks 1–3)
> **Goal:** Core parsing, basic AI generation for one combo (Java + Selenium + TestNG)

```mermaid
gantt
    title Phase 1 - Foundation
    dateFormat  YYYY-MM-DD
    section Backend Setup
    FastAPI project setup           :a1, 2026-10-20, 2d
    Database & models               :a2, after a1, 2d
    File upload API                 :a3, after a2, 2d
    section Parsers
    Excel parser                    :b1, after a3, 3d
    DOCX parser                     :b2, after b1, 2d
    HTML analyzer                   :b3, after b1, 3d
    section AI Core
    LLM orchestrator (OpenAI)       :c1, after a3, 3d
    Prompt templates v1             :c2, after c1, 3d
    section Generator
    Java + Selenium + TestNG gen    :d1, after c2, 5d
    ExtentReports integration       :d2, after d1, 2d
```

**Deliverables:**
- [x] Upload Excel/DOCX → parse to structured test cases
- [x] Analyze HTML → extract locators
- [x] Generate Java + Selenium + TestNG project with POM
- [x] ExtentReports integrated
- [x] API endpoints working

### Phase 2: Multi-Language & Tools (Weeks 4–6)
> **Goal:** All language/tool combos, Vision AI, improved prompts

```mermaid
gantt
    title Phase 2 - Expansion
    dateFormat  YYYY-MM-DD
    section Generators
    Java + Playwright generator      :a1, 2026-11-10, 3d
    Python + Selenium generator      :a2, after a1, 3d
    Python + Playwright generator    :a3, after a2, 3d
    JS + Playwright generator        :a4, after a3, 3d
    section AI Enhancement
    Vision AI (screenshot analysis)  :b1, 2026-11-10, 5d
    Multi-provider support (Gemini)  :b2, after b1, 3d
    Prompt optimization              :b3, after b2, 3d
    section Reports
    Allure integration               :c1, 2026-11-20, 3d
    Playwright HTML reporter         :c2, after c1, 2d
```

**Deliverables:**
- [x] All 7 language/tool combinations working
- [x] Screenshot analysis via Vision AI
- [x] Multiple AI provider support
- [x] Allure & Playwright reports

### Phase 3: Web Dashboard (Weeks 7–9)
> **Goal:** Full React dashboard with live features

```mermaid
gantt
    title Phase 3 - Dashboard
    dateFormat  YYYY-MM-DD
    section Frontend
    React project setup              :a1, 2026-12-01, 2d
    Upload & config UI               :a2, after a1, 4d
    Code preview (Monaco)            :a3, after a2, 3d
    section Integration
    API integration                  :b1, after a2, 3d
    WebSocket live logs              :b2, after b1, 3d
    section Features
    Test execution from UI           :c1, after b2, 3d
    Report viewer                    :c2, after c1, 2d
    Project download as ZIP          :c3, after c2, 2d
```

**Deliverables:**
- [x] Drag-and-drop file upload
- [x] Language/tool/framework configuration panel
- [x] Live code preview with Monaco editor
- [x] Test execution with real-time logs
- [x] Report viewing and project download

### Phase 4: Polish & Advanced Features (Weeks 10–12)
> **Goal:** Production-ready with advanced capabilities

| Feature | Description |
|---|---|
| **Smart Locator Healing** | AI suggests alternative locators when elements change |
| **Test Data Generation** | AI generates edge-case test data |
| **BDD Support** | Generate Cucumber/Behave feature files |
| **CI/CD Templates** | Auto-generate GitHub Actions / Jenkins pipeline configs |
| **Project History** | Save, version, and compare generated projects |
| **Batch Processing** | Upload multiple test case sheets at once |
| **Docker Execution** | Run generated tests inside Docker containers |
| **Local LLM Support** | Ollama integration for offline use |

---

## 7. AI Prompt Architecture

### Example: Test Case → Java + Selenium Code

**Step 1 — System Prompt:**
```
You are a Senior SDET with 15+ years of experience in test automation.
You write clean, maintainable, production-grade automation code following 
Page Object Model (POM) design pattern. You use:
- Language: Java
- Tool: Selenium WebDriver 4
- Framework: TestNG
- Reports: ExtentReports 5
- Build: Maven

Code standards:
- Explicit waits (no Thread.sleep)
- Descriptive method names
- Proper assertions with messages
- Screenshots on failure
- Proper logging
```

**Step 2 — Context Injection:**
```
## Test Case:
{parsed_test_case_json}

## Available Locators:
{locator_map_from_html_analysis}

## Screenshot Analysis:
{vision_ai_output}
```

**Step 3 — Generation Prompt:**
```
Generate the following files for this test case:
1. Page Object class with all element locators and action methods
2. Test class with test method implementing all steps
3. Update to testng.xml if needed

Requirements:
- Use WebDriverWait for all element interactions
- Add ExtentReports logging for each step
- Capture screenshot on assertion failure
- Use @DataProvider if test data varies
- Add proper JavaDoc comments
```

---

## 8. Sample Generated Output (Java + Selenium + TestNG)

### LoginPage.java (Page Object)
```java
public class LoginPage extends BasePage {
    
    // Locators
    @FindBy(id = "username")
    private WebElement usernameInput;
    
    @FindBy(id = "password") 
    private WebElement passwordInput;
    
    @FindBy(css = "button[type='submit']")
    private WebElement loginButton;
    
    @FindBy(css = ".error-message")
    private WebElement errorMessage;

    public LoginPage(WebDriver driver) {
        super(driver);
        PageFactory.initElements(driver, this);
    }

    public void enterUsername(String username) {
        wait.until(ExpectedConditions.visibilityOf(usernameInput));
        usernameInput.clear();
        usernameInput.sendKeys(username);
        ExtentLogger.info("Entered username: " + username);
    }

    public void enterPassword(String password) {
        wait.until(ExpectedConditions.visibilityOf(passwordInput));
        passwordInput.clear();
        passwordInput.sendKeys(password);
        ExtentLogger.info("Entered password: ****");
    }

    public DashboardPage clickLogin() {
        wait.until(ExpectedConditions.elementToBeClickable(loginButton));
        loginButton.click();
        ExtentLogger.info("Clicked Login button");
        return new DashboardPage(driver);
    }
}
```

### LoginTest.java (Test Class)
```java
@Listeners(ExtentReportListener.class)
public class LoginTest extends BaseTest {

    @Test(description = "TC001: Verify user login with valid credentials")
    public void testValidLogin() {
        LoginPage loginPage = new LoginPage(driver);
        
        ExtentLogger.step("Step 1: Navigate to login page");
        driver.get(ConfigReader.getProperty("base.url") + "/login");
        Assert.assertTrue(loginPage.isPageLoaded(), 
            "Login page should be displayed");

        ExtentLogger.step("Step 2: Enter username");
        loginPage.enterUsername("testuser@example.com");

        ExtentLogger.step("Step 3: Enter password");
        loginPage.enterPassword("SecurePass123");

        ExtentLogger.step("Step 4: Click login button");
        DashboardPage dashboard = loginPage.clickLogin();
        Assert.assertTrue(dashboard.isPageLoaded(), 
            "User should be redirected to dashboard");
    }
}
```

---

## 9. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload/testcases` | Upload Excel/DOCX test case files |
| `POST` | `/api/upload/html` | Upload HTML source code |
| `POST` | `/api/upload/screenshots` | Upload UI screenshots |
| `POST` | `/api/generate` | Trigger code generation with config |
| `GET` | `/api/generate/{job_id}/status` | Check generation status |
| `GET` | `/api/generate/{job_id}/preview` | Preview generated code |
| `GET` | `/api/generate/{job_id}/download` | Download project as ZIP |
| `POST` | `/api/execute/{project_id}` | Execute generated tests |
| `WS` | `/ws/execution/{job_id}` | WebSocket for live execution logs |
| `GET` | `/api/projects` | List all generated projects |
| `GET` | `/api/reports/{project_id}` | View test reports |

---

## 10. Configuration & Environment

### `.env` Configuration
```env
# AI Providers
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
GEMINI_API_KEY=AI...
GEMINI_MODEL=gemini-1.5-pro
OLLAMA_BASE_URL=http://localhost:11434
ACTIVE_AI_PROVIDER=openai  # openai | gemini | ollama

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/autotestai

# Redis
REDIS_URL=redis://localhost:6379

# Storage
UPLOAD_DIR=./uploads
OUTPUT_DIR=./generated
MAX_UPLOAD_SIZE_MB=50

# App
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000
```

---

## 11. Deployment Architecture

```mermaid
graph TB
    subgraph Docker["🐳 Docker Compose Stack"]
        A["Frontend<br/>React (Nginx)"]
        B["Backend<br/>FastAPI (Uvicorn)"]
        C["Worker<br/>Celery"]
        D["Redis<br/>Cache + Queue"]
        E["PostgreSQL<br/>Database"]
        F["MinIO<br/>File Storage"]
    end
    
    G["User Browser"] --> A
    A --> B
    B --> C
    B --> D
    B --> E
    B --> F
    C --> D
    C --> E
    C --> F
    
    B -->|API| H["OpenAI / Gemini"]
    C -->|API| H
```

---

## 12. Risk Assessment & Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| LLM generates incorrect code | High | Multi-pass validation, syntax checking, self-review prompt |
| Excel/DOCX format varies wildly | Medium | AI-powered flexible parsing, user-defined column mapping |
| Locator instability | Medium | Multi-strategy locators, healing mechanism |
| API costs (LLM calls) | Medium | Response caching, local LLM fallback, prompt optimization |
| Complex test scenarios | High | Iterative generation with context window management |
| Rate limiting from AI providers | Medium | Queue-based processing, retry with backoff |

---

## 13. Success Metrics

| Metric | Target |
|---|---|
| **Code Compilation Rate** | >95% of generated projects compile/run without manual edits |
| **Test Accuracy** | >90% of generated tests correctly implement the manual test steps |
| **Locator Accuracy** | >85% of auto-detected locators work on first try |
| **Generation Time** | <60 seconds for a single test case, <5 min for a full suite |
| **Language Coverage** | 100% — all 7 combo variations working |
| **User Satisfaction** | >4.0/5.0 rating from testers |

---

## 14. Immediate Next Steps

> [!IMPORTANT]
> **Ready to start building? Here's the recommended execution order:**

| Step | Action | Priority |
|---|---|---|
| 1 | Set up FastAPI backend with project structure | 🔴 Critical |
| 2 | Build Excel & DOCX parsers | 🔴 Critical |
| 3 | Build HTML analyzer & locator engine | 🔴 Critical |
| 4 | Integrate OpenAI API with prompt templates | 🔴 Critical |
| 5 | Create Java + Selenium + TestNG code generator | 🔴 Critical |
| 6 | Add ExtentReports template | 🟡 High |
| 7 | Build remaining language/tool generators | 🟡 High |
| 8 | Add Vision AI for screenshots | 🟡 High |
| 9 | Build React dashboard | 🟢 Medium |
| 10 | Add Docker deployment | 🟢 Medium |
| 11 | Add CI/CD template generation | 🔵 Nice-to-have |
| 12 | Add BDD/Cucumber support | 🔵 Nice-to-have |

---

> [!TIP]
> This plan is designed to be **iterative**. Phase 1 alone delivers a working MVP that can parse test cases and generate Java + Selenium projects. Each subsequent phase adds more languages, tools, and features.

**Estimated Total Timeline:** 10–12 weeks for full implementation  
**MVP (Phase 1) Timeline:** 3 weeks
