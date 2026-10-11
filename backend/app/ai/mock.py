import json

MOCK_EXPLAIN = json.dumps({
    "topic_type": "concept",
    "simple_explanation": "A stack is a linear data structure that follows the Last-In, First-Out (LIFO) principle. Think of it like a stack of plates where you add and remove from the top.",
    "exam_answer": "1) Definition: A stack is a linear data structure following the LIFO principle.\n2) Key Points:\n- Elements are added and removed only from the top.\n- Push adds an element to the stack.\n- Pop removes the top element.\n- Peek views the top element without removing it.\n3) Example: A pile of plates where the last placed plate is taken first."
})

SAMPLE_EXPLAIN_JSON = MOCK_EXPLAIN

MOCK_QUIZ = json.dumps([
    {
        "id": 1,
        "type": "mcq",
        "question": "What principle does a Stack data structure follow?",
        "options": ["FIFO (First In First Out)", "LIFO (Last In First Out)", "Random Access", "Priority Order"],
        "correct_answer": "LIFO (Last In First Out)",
        "explanation": "Stacks always insert and remove elements from the top end using LIFO.",
        "topic": "Stack Principle"
    },
    {
        "id": 2,
        "type": "mcq",
        "question": "Which operation is used to add an item to the top of a stack?",
        "options": ["pop", "enqueue", "push", "dequeue"],
        "correct_answer": "push",
        "explanation": "Push inserts an item onto the top of the stack.",
        "topic": "Stack Operations"
    },
    {
        "id": 3,
        "type": "mcq",
        "question": "What condition occurs when attempting to pop from an empty stack?",
        "options": ["Overflow", "Underflow", "Memory Leak", "Segmentation Fault"],
        "correct_answer": "Underflow",
        "explanation": "Removing an item when the stack is empty causes an underflow error.",
        "topic": "Error Handling"
    },
    {
        "id": 4,
        "type": "mcq",
        "question": "In Python, which list method corresponds directly to the push operation?",
        "options": ["insert(0, item)", "append(item)", "extend(item)", "add(item)"],
        "correct_answer": "append(item)",
        "explanation": "list.append() appends to the end of the list in O(1) time.",
        "topic": "Python Implementation"
    },
    {
        "id": 5,
        "type": "short",
        "question": "What does LIFO stand for, and why is it used to describe a stack?",
        "options": [],
        "correct_answer": "LIFO stands for Last In, First Out; the most recently added item is the first one removed.",
        "explanation": "LIFO means the last element pushed onto the stack is the first element popped off.",
        "topic": "LIFO Concept"
    }
])

SAMPLE_QUIZ_JSON = MOCK_QUIZ

MOCK_TRANSCRIPTION = "Sample transcribed study notes from image: Stacks follow LIFO principles."

MOCK_SIMULATION_NONE = "none"

MOCK_ASK = json.dumps({
    "answer": "A stack is a linear data structure following the LIFO (Last-In, First-Out) principle. The last item inserted is the first item removed.",
    "citations": [
        {
            "chunk_id": "chunk-mock-1",
            "page": 1,
            "snippet": "Stacks follow LIFO principles. Push inserts an item and pop removes an item."
        }
    ],
    "confidence": "high",
    "warnings": []
})

MOCK_CLASSIFY = "simulation"
