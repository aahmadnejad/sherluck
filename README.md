![Python](https://img.shields.io/badge/Python-3.6%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Offensive](https://img.shields.io/badge/Purpose-Offensive%20Redteam-red)
![John](https://img.shields.io/badge/Integration-John%20The%20Ripper-orange)

# Sherluck - Advanced Personal Data Wordlist Generator

<img src="./SherluckLogo.png" alt="Sherluck Icon" width="350"/>

Sherluck is a powerful Python-based wordlist generator designed for cybersecurity professionals, penetration testers, and security researchers. It creates comprehensive password wordlists from personal data using advanced pattern recognition, leet speak transformations, and intelligent combinations with built-in John the Ripper integration.

## Features

- **Multi-format Support**: Handles both single values and arrays in JSON input
- **Weighted Generation**: Prioritizes words based on importance weights
- **Realistic Leet Speak**: Creates natural leet variations (amir → @m!r, p@ssw0rd)
- **Smart Combinations**: Generates 2-word combinations with various separators
- **Date Intelligence**: Extracts and utilizes date components from birthdates and anniversaries
- **Prefix/Suffix Integration**: Applies common prefixes and suffixes to enhance word variations
- **External Wordlists**: Optional integration with popular wordlists (rockyou, common passwords, etc.)
- **Multi-threading**: Parallel processing for faster generation
- **Length Filtering**: Customizable minimum and maximum password lengths
- **John the Ripper Integration**: Direct execution with generated wordlists
- **Realistic Patterns**: Generates human-like password patterns with mixed complexity

## Installation

```bash
git clone https://github.com/yourusername/sherluck.git
cd sherluck

pip install requests
chmod +x sherluck.py
```

## Basic Usage

```bash
python sherluck.py -i person.json -o wordlist.txt
```

## Advanced Usage

### Wordlist Generation Options

```bash
# With common wordlists and custom length
python sherluck.py -i person.json -o wordlist.txt --include-common --min-length 6 --max-length 25

# Disable multi-threading for older systems
python sherluck.py -i person.json -o wordlist.txt --no-threading

# Use specific common wordlists
python sherluck.py -i person.json -o wordlist.txt --include-common --common-lists rockyou common_passwords

# Limit wordlist size
python sherluck.py -i person.json -o wordlist.txt -m 50000
```

### John the Ripper Integration

```bash
# Basic John the Ripper execution
python sherluck.py -i person.json -o wordlist.txt --john --john-target hashes.txt

# John with specific hash format
python sherluck.py -i person.json -o wordlist.txt --john --john-target hashes.txt --john-format raw-md5

# John with rules enabled
python sherluck.py -i person.json -o wordlist.txt --john --john-target hashes.txt --john-rules

# Multiple target files
python sherluck.py -i person.json -o wordlist.txt --john --john-target hash1.txt hash2.txt hash3.txt

# Different John modes
python sherluck.py -i person.json -o wordlist.txt --john --john-command with_rules --john-target hashes.txt
```

## Weighting System
Sherluck uses a sophisticated weighting system to prioritize words:

- Field-specific weights: Override category weights for specific fields
- Category weights: Apply to groups of related fields
- Automatic weight decay: Leet variations and combinations get slightly reduced weights

## John the Ripper Commands
Sherluck supports multiple John the Ripper modes:

- basic_crack - Standard wordlist attack
- incremental - Incremental mode attack
- single_crack - Single crack mode
- with_rules - Wordlist with rules enabled
- specific_format - Specify hash format (e.g., raw-md5, nt)
- show_cracked - Show previously cracked passwords
- restore_session - Restore interrupted session
- multi_crack - Crack multiple target files simultaneously

## Contributing

Contributions are welcome! Please feel free to:

- Submit pull requests for new features
- Open issues for bugs and feature requests
- Improve documentation
- Add new leet speak patterns or wordlists
- Optimize performance and memory usage