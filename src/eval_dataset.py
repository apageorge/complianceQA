EVAL_DATASET = [

    # --- Core Concept: Consumer Duty ---
    {
        "question": "What is the Consumer Duty and what does it aim to achieve?",
        "expected_keywords": ["standard of care", "good outcomes", "retail customers"],
        "should_answer": True
    },
    {
        "question": "What is the Consumer Principle under the FCA Consumer Duty?",
        "expected_keywords": ["act", "good outcomes", "retail customers"],
        "should_answer": True
    },

    # --- Cross-cutting rules ---
    {
        "question": "What are the cross-cutting rules under the Consumer Duty?",
        "expected_keywords": ["good faith", "foreseeable harm", "financial objectives"],
        "should_answer": True
    },
    {
        "question": "What does acting in good faith mean in the context of Consumer Duty?",
        "expected_keywords": ["honest", "fair", "customers"],
        "should_answer": True
    },

    # --- Four Outcomes ---
    {
        "question": "What are the four outcomes defined under the Consumer Duty?",
        "expected_keywords": ["products", "price", "understanding", "support"],
        "should_answer": True
    },
    {
        "question": "What is the price and value outcome under Consumer Duty?",
        "expected_keywords": ["fair value", "price", "quality"],
        "should_answer": True
    },
    {
        "question": "What is the consumer understanding outcome?",
        "expected_keywords": ["communication", "understand", "informed decisions"],
        "should_answer": True
    },
    {
        "question": "What is the consumer support outcome?",
        "expected_keywords": ["support", "barriers", "customer"],
        "should_answer": True
    },

    # --- Scope ---
    {
        "question": "Who does the Consumer Duty apply to?",
        "expected_keywords": ["retail customers", "firms", "regulated"],
        "should_answer": True
    },
    {
        "question": "Does the Consumer Duty apply to prospective customers or only existing customers?",
        "expected_keywords": ["prospective", "actual customers"],
        "should_answer": True
    },
    {
        "question": "What types of firms are included in the distribution chain under Consumer Duty?",
        "expected_keywords": ["manufacture", "distribution", "customer outcomes"],
        "should_answer": True
    },

    # --- Governance & Accountability ---
    {
        "question": "What responsibilities do boards or senior management have under Consumer Duty?",
        "expected_keywords": ["board", "accountability", "outcomes"],
        "should_answer": True
    },
    {
        "question": "How should firms monitor customer outcomes under the Consumer Duty?",
        "expected_keywords": ["monitor", "review", "outcomes"],
        "should_answer": True
    },

    # --- Vulnerable customers ---
    {
        "question": "How does the Consumer Duty address customers in vulnerable circumstances?",
        "expected_keywords": ["vulnerability", "needs", "risk"],
        "should_answer": True
    },

    # --- Regulatory intent ---
    {
        "question": "Why did the FCA introduce the Consumer Duty?",
        "expected_keywords": ["consumer protection", "better outcomes", "innovation"],
        "should_answer": True
    },
    {
        "question": "How does the Consumer Duty differ from Principles 6 and 7?",
        "expected_keywords": ["higher standard", "broader", "consumer protection"],
        "should_answer": True
    },

    # --- Negative / fallback cases (VERY IMPORTANT) ---
    {
        "question": "What are the tax implications of Consumer Duty for firms?",
        "expected_keywords": [],
        "should_answer": False
    },
    {
        "question": "What is the holiday entitlement policy for FCA employees?",
        "expected_keywords": [],
        "should_answer": False
    }
]