#!/usr/bin/env python3

import json
import argparse
import sys
import itertools
import os
import requests
import threading
import queue
import time
import subprocess
import tempfile
from typing import List, Dict, Any, Set, Union, Tuple, Generator
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

class Sherluck:
    def __init__(self):
        self.leet_speak_map = {
            'a': ['@', '4', '^', '/\\', 'λ'],
            'b': ['8', '6', '|3', 'ß'],
            'c': ['(', '<', '{', '[', '©'],
            'd': ['|)', '|]', 'Ð'],
            'e': ['3', '&', '€', '£'],
            'f': ['|=', 'ƒ', 'ph'],
            'g': ['6', '9', '&'],
            'h': ['#', '|-|', '}{'],
            'i': ['1', '!', '|', ']['],
            'j': ['_|', '_/', ']'],
            'k': ['X', '|<', '|{'],
            'l': ['1', '|', '7', '|_'],
            'm': ['|\\/|', '/\\/\\', '[V]'],
            'n': ['|\\|', '/\\/', '[\\]'],
            'o': ['0', '()', '[]', '°'],
            'p': ['|*', '|o', '|>'],
            'q': ['(_,)', '()_', '0_'],
            'r': ['|2', '|?', '|^'],
            's': ['5', '$', '§', 'z'],
            't': ['7', '+', '†'],
            'u': ['|_|', '(_)', '\\_\\'],
            'v': ['\\/', '|/', '\\|'],
            'w': ['\\/\\/', 'VV', '\\N'],
            'x': ['><', '}{', ')('],
            'y': ['`/', '¥', '\\|/'],
            'z': ['2', '%', 's']
        }
        
        self.common_suffixes = [
            '123', '1234', '12345', '123456', 
            '!', '!!', '!!!', '@', '@@', '#', '##', 
            '$', '$$', '%', '%%', '^', '&', '*',
            '00', '01', '99', '000', '001', '999',
            '0000', '1111', '2222', '9999',
            'password', 'pass', 'pwd', 'secret',
            'admin', 'root', 'user', 'login',
            'secure', 'security', 'safe'
        ]
        
        self.common_prefixes = [
            '!', '@', '#', '$', '%', '^', '&', '*', '~',
            'admin', 'root', 'super', 'my', 'the', 'our',
            'new', 'old', 'good', 'best', 'top',
            'secret', 'hidden', 'private', 'secure'
        ]

        self.common_wordlists = {
            'rockyou': 'https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt',
            'common_passwords': 'https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt',
            'english_words': 'https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt'
        }

        self.john_commands = {
            'basic_crack': 'john --wordlist={wordlist} {target}',
            'incremental': 'john --incremental {target}',
            'single_crack': 'john --single {target}',
            'with_rules': 'john --wordlist={wordlist} --rules {target}',
            'show_cracked': 'john --show {target}',
            'restore_session': 'john --restore',
            'specific_format': 'john --format={format} --wordlist={wordlist} {target}',
            'multi_crack': 'john --wordlist={wordlist} {target1} {target2} {target3}'
        }

    def run_john_the_ripper(self, command_key: str, wordlist_path: str, target_files: List[str], 
                           format_type: str = None, rules: bool = False) -> None:
        """
        Execute John the Ripper with the specified command
        """
        if command_key not in self.john_commands:
            print(f"[!] Unknown John command: {command_key}")
            print(f"[+] Available commands: {', '.join(self.john_commands.keys())}")
            return
        
        command_template = self.john_commands[command_key]
        command = command_template.format(
            wordlist=wordlist_path,
            target=' '.join(target_files),
            format=format_type or 'raw-md5'
        )
        
        if rules and '--rules' not in command:
            command += ' --rules'
        
        print(f"[+] Executing John the Ripper: {command}")
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=3600)
            print(f"[+] John output:\n{result.stdout}")
            if result.stderr:
                print(f"[!] John errors:\n{result.stderr}")
        except subprocess.TimeoutExpired:
            print("[!] John the Ripper execution timed out after 1 hour")
        except Exception as e:
            print(f"[!] Failed to execute John the Ripper: {e}")

    def download_wordlist(self, name: str, url: str, output_dir: str = "wordlists") -> str:
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"{name}.txt")
        
        if os.path.exists(filename):
            return filename
            
        try:
            print(f"[+] Downloading {name} wordlist...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[+] Downloaded {name} wordlist to {filename}")
            return filename
        except Exception as e:
            print(f"[!] Failed to download {name} wordlist: {e}")
            return None

    def load_external_wordlists(self, wordlist_names: List[str], max_words: int = 10000) -> Generator[str, None, None]:
        for name in wordlist_names:
            if name in self.common_wordlists:
                filename = self.download_wordlist(name, self.common_wordlists[name])
                if filename:
                    try:
                        count = 0
                        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                            for line in f:
                                word = line.strip()
                                if word and 4 <= len(word) <= 30:
                                    yield word
                                    count += 1
                                    if count >= max_words:
                                        break
                    except Exception as e:
                        print(f"[!] Error reading {name} wordlist: {e}")

    def load_data(self, filename: str) -> Dict[str, Any]:
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: File {filename} not found")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {filename}")
            sys.exit(1)

    def ensure_list(self, data: Any) -> List[Any]:
        if data is None:
            return []
        if isinstance(data, list):
            return data
        return [data]

    def generate_realistic_leet_variations(self, word: str, max_variations: int = 8) -> Generator[str, None, None]:
        """Generate more realistic leet variations with mixed complexity"""
        if not word or len(word) == 0:
            return
        
        yield word
        yield word.lower()
        yield word.upper()
        yield word.capitalize()
        
        variations_generated = 4
        
        simple_leet = word.lower()
        simple_subs = {
            'a': '@', 'e': '3', 'i': '1', 'o': '0', 's': '$', 't': '7'
        }
        
        for char, replacement in simple_subs.items():
            if char in simple_leet and variations_generated < max_variations:
                new_word = simple_leet.replace(char, replacement)
                yield new_word
                variations_generated += 1
                yield new_word.capitalize()
                variations_generated += 1

        if len(word) <= 6 and variations_generated < max_variations:
            for i in range(min(2, len(word))):
                char = word[i].lower()
                if char in self.leet_speak_map:
                    for replacement in self.leet_speak_map[char][:2]:
                        if variations_generated >= max_variations:
                            return
                        new_word = word[:i] + replacement + word[i+1:]
                        yield new_word
                        variations_generated += 1

    def apply_prefixes_suffixes(self, word: str, max_combinations: int = 12) -> Generator[str, None, None]:
        yield word
        count = 1
        
        for suffix in ['123', '1234', '1', '2', '!', '']:
            if count >= max_combinations:
                return
            yield f"{word}{suffix}"
            count += 1
        
        for prefix in ['', '!', '1', '2']:
            if count >= max_combinations:
                return
            yield f"{prefix}{word}"
            count += 1
        
        special_combos = [f"{word}_{n}" for n in ['123', '2024', '99']] + \
                        [f"{n}{word}" for n in ['1', '2', '99']]
        
        for combo in special_combos:
            if count >= max_combinations:
                return
            yield combo
            count += 1

    def extract_dates_from_data(self, data: Dict[str, Any]) -> Set[str]:
        dates = set()
        
        date_fields = ['birthdate', 'anniversary', 'important_date', 
                      'child_birthdate', 'children_birthdates', 'spouse_birthdate',
                      'marriage_date', 'graduation_date', 'employment_date']
        
        for field in date_fields:
            field_data = data.get(field)
            if field_data:
                for item in self.ensure_list(field_data):
                    dates.update(self.parse_date(str(item)))
        
        return dates

    def parse_date(self, date_str: str) -> Set[str]:
        components = set()
        
        try:
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    components.update([
                        str(date_obj.year),
                        str(date_obj.year)[2:],
                        str(date_obj.month).zfill(2),
                        str(date_obj.day).zfill(2),
                    ])
                    break
                except ValueError:
                    continue
        except:
            numbers = re.findall(r'\d+', date_str)
            components.update(numbers)
        
        return components

    def extract_keywords(self, data: Dict[str, Any], weights: Dict[str, float] = None) -> Generator[Tuple[str, float], None, None]:
        if weights is None:
            weights = {}
            
        default_weight = 1.0
        
        field_categories = {
            'basic': ['firstname', 'lastname', 'middlename', 'nickname', 'username'],
            'family': ['mother_maiden_name', 'father_name', 'family_name', 'spouse_name',
                      'child_name', 'children_names', 'pet_name'],
            'relationships': ['girlfriend_names', 'boyfriend_names', 'friend_names',
                            'partner_names', 'ex_girlfriend_names', 'ex_boyfriend_names'],
            'location': ['city', 'birth_city', 'country', 'birth_country', 'state',
                        'birth_state', 'hometown', 'street', 'zipcode', 'postal_code'],
            'education': ['school', 'university', 'college', 'high_school', 'elementary_school'],
            'work': ['workplace', 'company', 'employer', 'department', 'team', 'project_name'],
            'numbers': ['id_card', 'passport_number', 'driver_license_number', 'phone_number',
                       'student_id', 'employee_id', 'social_security', 'insurance_number'],
            'favorites': ['favorite_color', 'favorite_movie', 'favorite_book', 'favorite_team',
                         'favorite_player', 'favorite_food', 'favorite_restaurant']
        }
        
        for category, fields in field_categories.items():
            for field in fields:
                field_data = data.get(field)
                if field_data:
                    weight = weights.get(field, weights.get(category, default_weight))
                    for item in self.ensure_list(field_data):
                        if item and str(item).strip():
                            yield (str(item).strip(), weight)
        
        date_components = self.extract_dates_from_data(data)
        for date_component in date_components:
            yield (date_component, weights.get('dates', default_weight))

    def generate_word_variations(self, word: str, weight: float) -> Generator[Tuple[str, float], None, None]:
        yield (word, weight)
        yield (word.lower(), weight)
        yield (word.upper(), weight * 0.9)
        yield (word.capitalize(), weight * 0.9)
        
        leet_variations = set()
        for leet_word in self.generate_realistic_leet_variations(word):
            leet_variations.add(leet_word)
        
        for leet_word in leet_variations:
            yield (leet_word, weight * 0.8)
            
            for ps_word in self.apply_prefixes_suffixes(leet_word, 4):
                yield (ps_word, weight * 0.7)
        
        for ps_word in self.apply_prefixes_suffixes(word, 4):
            yield (ps_word, weight * 0.7)

    def generate_combinations(self, keywords: List[Tuple[str, float]], max_combinations: int = 20000) -> Generator[Tuple[str, float], None, None]:
        if not keywords:
            return
            
        seen_combinations = set()
        count = 0
        
        for word, weight in keywords:
            if word not in seen_combinations:
                yield (word, weight)
                seen_combinations.add(word)
                count += 1
                if count >= max_combinations:
                    return
        
        separators = ['', '_', '.', '-']
        
        for i in range(len(keywords)):
            for j in range(i + 1, len(keywords)):
                if count >= max_combinations:
                    return
                
                word1, weight1 = keywords[i]
                word2, weight2 = keywords[j]
                total_weight = (weight1 + weight2) / 2
                
                for sep in separators:
                    combo1 = f"{word1}{sep}{word2}"
                    if combo1 not in seen_combinations:
                        yield (combo1, total_weight)
                        seen_combinations.add(combo1)
                        count += 1
                        if count >= max_combinations:
                            return
                    
                    combo2 = f"{word2}{sep}{word1}"
                    if combo2 not in seen_combinations:
                        yield (combo2, total_weight)
                        seen_combinations.add(combo2)
                        count += 1
                        if count >= max_combinations:
                            return

    def add_numeric_patterns(self, words: List[Tuple[str, float]], date_components: Set[str], max_patterns: int = 10000) -> Generator[Tuple[str, float], None, None]:
        numbers = list(date_components)
        
        common_numbers = [str(i) for i in range(0, 20)]
        common_numbers.extend(['123', '1234', '12345', '111', '222', '333'])
        numbers.extend(common_numbers)
        
        count = 0
        seen_patterns = set()
        
        for word, weight in words:
            if word not in seen_patterns:
                yield (word, weight)
                seen_patterns.add(word)
                count += 1
            
            if count >= max_patterns:
                return
                
            for number in numbers[:8]:
                patterns = [
                    f"{word}{number}",
                    f"{number}{word}",
                    f"{word}_{number}",
                    f"{number}_{word}"
                ]
                
                for pattern in patterns:
                    if pattern not in seen_patterns and count < max_patterns:
                        yield (pattern, weight * 0.9)
                        seen_patterns.add(pattern)
                        count += 1
                        if count >= max_patterns:
                            return

    def generate_wordlist(self, data: Dict[str, Any], max_words: int = 100000,
                         min_length: int = 4, max_length: int = 30, 
                         use_threading: bool = True, weights: Dict[str, float] = None,
                         include_common: bool = False, common_wordlists: List[str] = None) -> Generator[str, None, None]:
        
        if common_wordlists is None:
            common_wordlists = ['rockyou']
        
        print("[+] Extracting keywords with weights...")
        keywords_with_weights = list(self.extract_keywords(data, weights))
        print(f"[+] Found {len(keywords_with_weights)} base keywords")
        
        print("[+] Generating word variations...")
        all_variations = []
        variation_count = 0
        for word, weight in keywords_with_weights:
            for variation, var_weight in self.generate_word_variations(word, weight):
                if variation_count < 50000:
                    all_variations.append((variation, var_weight))
                    variation_count += 1
        print(f"[+] Generated {variation_count} variations")
        
        print("[+] Generating combinations...")
        combinations = []
        combo_count = 0
        for combo, weight in self.generate_combinations(all_variations, 30000):
            if combo_count < 30000:
                combinations.append((combo, weight))
                combo_count += 1
        print(f"[+] Generated {combo_count} combinations")
        
        print("[+] Adding numeric patterns...")
        date_components = self.extract_dates_from_data(data)
        final_count = 0
        
        for word, weight in self.add_numeric_patterns(combinations, date_components, max_words):
            if min_length <= len(word) <= max_length and final_count < max_words:
                yield word
                final_count += 1
        
        if include_common and final_count < max_words:
            print("[+] Adding common wordlists...")
            common_count = 0
            for common_word in self.load_external_wordlists(common_wordlists, max_words // 5):
                if final_count < max_words:
                    yield common_word
                    final_count += 1
                    common_count += 1
            print(f"[+] Added {common_count} common words")
        
        print(f"[+] Final wordlist contains {final_count} words")

    def save_wordlist(self, wordlist_generator: Generator[str, None, None], filename: str, max_words: int):
        count = 0
        with open(filename, 'w', encoding='utf-8') as f:
            for word in wordlist_generator:
                if count >= max_words:
                    break
                f.write(word + '\n')
                count += 1
                if count % 10000 == 0:
                    print(f"[+] Written {count} words so far...")
        
        print(f"[+] Wordlist saved to {filename} with {count} words")

def create_template_json():
    template = {
        "firstname": "amir",
        "lastname": "hosseini",
        "nickname": "amirhos",
        "birthdate": "1999-08-15",
        "pet_name": "max",
        "city": "tehran",
        "birth_city": "mashhad",
        "country": "iran",
        "school": "tehran university",
        "workplace": "rayan fanavaran company",
        "id_card": "1234567890",
        "phone_number": "09123456789",
        "hobbies": ["programming", "gaming", "reading"],
        "interests": ["cybersecurity", "ai", "machine learning"],
        
        "weights": {
            "basic": 1.0,
            "family": 0.9,
            "relationships": 0.8,
            "education": 0.7,
            "work": 0.6,
            "favorites": 0.8,
            "dates": 0.9,
            "firstname": 1.2,
            "lastname": 1.1
        }
    }
    
    with open('sherluck_template.json', 'w') as f:
        json.dump(template, f, indent=2)
    
    print("[+] Template JSON file created: sherluck_template.json")

def main():
    parser = argparse.ArgumentParser(description="Sherluck - Advanced Personal Data Wordlist Generator")
    parser.add_argument("-i", "--input", help="Input JSON file with personal data")
    parser.add_argument("-o", "--output", required=True, help="Output wordlist file")
    parser.add_argument("-m", "--max-words", type=int, default=100000, help="Maximum words to generate (default: 100000)")
    parser.add_argument("--min-length", type=int, default=4)
    parser.add_argument("--max-length", type=int, default=30)
    parser.add_argument("--no-threading", action="store_true", help="Disable multithreading")
    parser.add_argument("--include-common", action="store_true", help="Include common wordlists")
    parser.add_argument("--common-lists", nargs='+', default=['rockyou'], 
                       choices=['rockyou', 'common_passwords', 'english_words'],
                       help="Common wordlists to include")
    parser.add_argument("--create-template", action="store_true", help="Create a template JSON file")
    
    parser.add_argument("--john", action="store_true", help="Run John the Ripper after generating wordlist")
    parser.add_argument("--john-command", default="basic_crack", help="John the Ripper command to execute")
    parser.add_argument("--john-target", nargs='+', help="Target files for John the Ripper")
    parser.add_argument("--john-format", help="Hash format for John the Ripper")
    parser.add_argument("--john-rules", action="store_true", help="Use rules with John the Ripper")
    
    args = parser.parse_args()
    
    print("""
    ███████╗██╗  ██╗███████╗██████╗ ██╗      ██╗   ██╗ ██████╗██╗  ██╗
    ██╔════╝██║  ██║██╔════╝██╔══██╗██║      ██║   ██║██╔════╝██║ ██╔╝
    ███████╗███████║█████╗  ██████╔╝██║      ██║   ██║██║     █████╔╝ 
    ╚════██║██╔══██║██╔══╝  ██╔══██╗██║      ██║   ██║██║     ██╔═██╗ 
    ███████║██║  ██║███████╗██║  ██║███████╗╚██████╔╝╚██████╗██║  ██╗
    ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝
    |                                                             |
    |               Advanced Wordlist Generator                   |
    |_____________________________________________________________|
    """)
    
    if args.create_template:
        create_template_json()
        return
    
    if not args.input:
        print("Error: You must specify an input file")
        print("Use --create-template to generate a template JSON file")
        sys.exit(1)
    
    generator = Sherluck()
    
    data = generator.load_data(args.input)
    weights = data.get('weights', {})
    
    print(f"[+] Generating up to {args.max_words} words...")
    wordlist_generator = generator.generate_wordlist(
        data=data,
        max_words=args.max_words,
        min_length=args.min_length,
        max_length=args.max_length,
        use_threading=not args.no_threading,
        weights=weights,
        include_common=args.include_common,
        common_wordlists=args.common_lists
    )
    
    generator.save_wordlist(wordlist_generator, args.output, args.max_words)
    
    if args.john:
        if not args.john_target:
            print("[!] Please specify target files for John the Ripper using --john-target")
        else:
            print("[+] Starting John the Ripper...")
            generator.run_john_the_ripper(
                command_key=args.john_command,
                wordlist_path=args.output,
                target_files=args.john_target,
                format_type=args.john_format,
                rules=args.john_rules
            )
    
    print("[+] Generation complete!")

if __name__ == "__main__":
    main()