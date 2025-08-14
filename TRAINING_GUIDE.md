# GPT Model Training Guide for SnapGrade

This guide will walk you through training a custom GPT model on your grading data to improve SnapGrade's performance for your specific use case.

## 📁 Where to Keep Your Dataset

**Place your training data in the `dataset/` folder:**

```
SnapGrade-Beta-main 2/
├── dataset/                    ← PUT YOUR DATA HERE
│   ├── README.md              ← Instructions and examples
│   ├── sample_training_data.json ← Example format
│   ├── your_data_file1.json   ← Your actual training data
│   ├── your_data_file2.csv    ← You can use multiple files
│   └── more_data.json         ← Any number of JSON/CSV files
├── grader/
│   └── fine_tuning.py         ← Training logic
├── train_model.py             ← Training script
└── ...
```

## 📊 Data Format Requirements

### JSON Format (Recommended)
```json
[
    {
        "submission": "Student's answer text",
        "rubric": "Grading rubric text",
        "score": "8/10" or "85",
        "feedback": "Detailed feedback text"
    }
]
```

### CSV Format
```csv
submission,rubric,score,feedback
"Student answer","Rubric text","8/10","Feedback text"
```

## 🚀 Step-by-Step Training Process

### Step 1: Prepare Your Data
1. Collect your grading examples (submissions, rubrics, scores, feedback)
2. Format them as JSON or CSV files
3. Place files in the `dataset/` folder
4. Ensure you have at least 50-100 examples for good results

### Step 2: Set Up OpenAI API
1. Make sure you have an OpenAI API key with fine-tuning access
2. Ensure your `.env` file contains: `OPENAI_API_KEY=your_api_key_here`
3. Fine-tuning requires a paid OpenAI account

### Step 3: Run the Training Script

**Basic training:**
```bash
python3 train_model.py --dataset ./dataset
```

**Advanced options:**
```bash
# Use GPT-4 as base model (more expensive but potentially better)
python3 train_model.py --dataset ./dataset --model gpt-4

# Add a custom suffix to your model name
python3 train_model.py --dataset ./dataset --suffix "my-school-grader"

# Start training but don't wait for completion
python3 train_model.py --dataset ./dataset --no-wait
```

### Step 4: Monitor Training Progress

**If you used `--no-wait`, check status:**
```bash
python3 train_model.py --check-status ft-job-abc123
```

**Training typically takes:**
- 10-30 minutes for small datasets (50-200 examples)
- 30-60 minutes for medium datasets (200-1000 examples)
- 1-3 hours for large datasets (1000+ examples)

### Step 5: Use Your Trained Model

1. **Update your `.env` file:**
   ```
   OPENAI_MODEL=ft:gpt-3.5-turbo-1106:your-org:your-suffix:abc123
   ```

2. **Restart your SnapGrade server:**
   ```bash
   # Stop current server (Ctrl+C)
   # Then restart:
   python3 app.py
   ```

3. **Your custom model is now active!**

## 💡 Tips for Better Results

### Data Quality
- **Quality over Quantity**: 100 excellent examples > 1000 poor ones
- **Diverse Content**: Include various assignment types and difficulty levels
- **Balanced Scores**: Include examples across the full score range (not just A's or F's)
- **Detailed Feedback**: The more detailed your training feedback, the better

### Score Formats
- **Fraction format**: "8/10", "15/20" (recommended for specific rubrics)
- **Percentage format**: "85", "92" (for percentage-based grading)
- **Be consistent** within each dataset file

### Rubric Consistency
- Use similar rubric formats to what you'll use in production
- Include point breakdowns when possible
- Be specific about grading criteria

## 🔧 Troubleshooting

### Common Issues

**"No valid training examples found"**
- Check your JSON/CSV format
- Ensure all required fields are present: submission, rubric, score, feedback
- Verify file encoding is UTF-8

**"OpenAI API error"**
- Verify your API key is correct and has fine-tuning access
- Check your OpenAI account has sufficient credits
- Ensure you're using a paid OpenAI account (fine-tuning not available on free tier)

**"Training job failed"**
- Check if your training data is too large (max ~50MB)
- Ensure examples are properly formatted
- Verify no examples are too long (max ~4000 tokens per example)

### Getting Help

1. **Check the logs**: Training script provides detailed error messages
2. **Validate your data**: Use the sample file as a reference
3. **Start small**: Try with 10-20 examples first to test the process

## 💰 Cost Considerations

**OpenAI Fine-tuning Costs (approximate):**
- Training: $0.008 per 1K tokens
- Usage: 8x the base model cost
- Example: 100 training examples ≈ $5-15 to train

**Cost-saving tips:**
- Start with gpt-3.5-turbo (cheaper than GPT-4)
- Use concise but complete training examples
- Test with small datasets first

## 🔄 Updating Your Model

To retrain with new data:
1. Add new examples to your dataset folder
2. Run the training script again
3. Update your `.env` file with the new model ID
4. Restart the server

## 📈 Measuring Improvement

**Before training:**
- Test SnapGrade on a few sample assignments
- Note the quality and consistency of scores/feedback

**After training:**
- Test the same assignments with your custom model
- Compare accuracy, consistency, and feedback quality
- Fine-tune further if needed

---

## Quick Start Checklist

- [ ] Prepare training data in JSON/CSV format
- [ ] Place data files in `dataset/` folder
- [ ] Ensure OpenAI API key is configured
- [ ] Run: `python3 train_model.py --dataset ./dataset`
- [ ] Wait for training to complete
- [ ] Update `.env` with new model ID
- [ ] Restart SnapGrade server
- [ ] Test improved grading performance

Your custom GPT model will now provide more accurate and consistent grading tailored to your specific requirements!