# Sahayak - AI-Powered Teaching Assistant

## High-Level Architectural Overview

The application is structured around a three-tiered architecture, optimized for offline-first functionality and efficient AI integration.

1.  **Presentation Layer (Flutter)**
    *   **UI/UX:** A clean, intuitive, and responsive UI built with Flutter. It will prioritize simplicity and performance to ensure a smooth experience even on low-end devices. Material Design principles will be used for a familiar and accessible interface.
    *   **Components:**
        *   Input Forms: For teachers to enter topics, grade levels, and local context keywords.
        *   Content Display: To render generated lesson plans, quizzes, and other educational materials.
        *   Chat Interface: For the "Educational Copilot" feature.
        *   Offline Library: To browse and manage saved content.

2.  **Business Logic Layer (Dart/Flutter)**
    *   **State Management:** A robust state management solution (like BLoC or Provider) will be used to manage the application's state, including user input, generated content, and connectivity status.
    *   **AI Service Abstraction:** A dedicated service layer will abstract the interactions with the AI models. This layer will be responsible for:
        *   Model Selection: Dynamically choosing between on-device (Gemini Nano) and cloud-based (Gemini Pro) models based on the task's complexity and network availability.
        *   Prompt Engineering: Constructing effective prompts based on user input and predefined templates.
        *   Offline Handling: Managing the queue of requests to be sent to the cloud when connectivity is restored.
    *   **Repository Pattern:** To abstract data sources (local database and cloud API), ensuring a clean separation of concerns.

3.  **Data Layer**
    *   **Local Database:** A lightweight, on-device database (like SQLite with the `sqflite` package) will be used to store:
        *   Generated content for offline access.
        *   User preferences and settings.
        *   Cached AI responses.
    *   **Cloud API:** For interacting with the Gemini Pro model when an internet connection is available.
    *   **Synchronization Service:** A background service will handle the synchronization of data between the local database and the cloud, ensuring that content is updated seamlessly.

---

## Boilerplate Code Snippets & Concepts

### 1. Interacting with Gemini API (Conceptual)

This snippet outlines a service to interact with a Gemini-like API.

```dart
// lib/services/ai_service.dart

import 'package:http/http.dart' as http;
import 'dart:convert';

class AIService {
  final String apiKey;
  final String cloudBasedUrl = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent";

  AIService({required this.apiKey});

  Future<String> generateContent(String prompt) async {
    // Check for connectivity, decide whether to use on-device or cloud model.
    // For this example, we'll use the cloud API.

    try {
      final response = await http.post(
        Uri.parse('$cloudBasedUrl?key=$apiKey'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'contents': [{'parts': [{'text': prompt}]}]
        }),
      );

      if (response.statusCode == 200) {
        final decodedResponse = json.decode(response.body);
        return decodedResponse['candidates'][0]['content']['parts'][0]['text'];
      } else {
        // Handle API errors (e.g., rate limiting, invalid key)
        print('API Error: ${response.body}');
        return "Error: Could not generate content.";
      }
    } catch (e) {
      // Handle network errors
      print('Network Error: $e');
      return "Error: Please check your internet connection.";
    }
  }
}
```

### 2. Handling Hyper-Local Context

Prompt engineering is key. The UI will collect local context, and the business logic will format it into the prompt.

```dart
// lib/utils/prompt_generator.dart

class PromptGenerator {
  static String forLessonPlan({
    required String topic,
    required String gradeLevel,
    required String language,
    List<String>? localKeywords,
  }) {
    String keywords = localKeywords?.join(', ') ?? 'general';
    return '''
    Generate a detailed lesson plan for a $gradeLevel class on the topic of "$topic".
    The lesson plan should be in $language.
    Incorporate the following local concepts, examples, or places to make it relatable for the students: $keywords.
    The lesson plan should include learning objectives, materials needed, step-by-step activities, and an assessment method.
    ''';
  }

  static String forQuiz({
    required String topic,
    required String gradeLevel,
    required int numQuestions,
  }) {
    return '''
    Create a quiz with $numQuestions multiple-choice questions for a $gradeLevel class on the topic of "$topic".
    Ensure the questions are clear and appropriate for the specified grade level.
    Provide the correct answer for each question.
    ''';
  }
}
```

### 3. Offline Data Storage (Conceptual)

Using `sqflite` to store generated content.

**Model Class:**
```dart
// lib/models/generated_content.dart

class GeneratedContent {
  final int? id;
  final String title;
  final String content;
  final DateTime createdAt;

  GeneratedContent({this.id, required this.title, required this.content, required this.createdAt});

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'title': title,
      'content': content,
      'createdAt': createdAt.toIso8601String(),
    };
  }
}
```

**Database Helper:**
```dart
// lib/services/database_helper.dart

import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/generated_content.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('sahayak.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(path, version: 1, onCreate: _createDB);
  }

  Future _createDB(Database db, int version) async {
    await db.execute('''
    CREATE TABLE generated_content (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      content TEXT NOT NULL,
      createdAt TEXT NOT NULL
    )
    ''');
  }

  Future<void> insertContent(GeneratedContent content) async {
    final db = await instance.database;
    await db.insert('generated_content', content.toMap());
  }

  Future<List<GeneratedContent>> getAllContent() async {
    final db = await instance.database;
    final maps = await db.query('generated_content', orderBy: 'createdAt DESC');

    return List.generate(maps.length, (i) {
      return GeneratedContent(
        id: maps[i]['id'] as int,
        title: maps[i]['title'] as String,
        content: maps[i]['content'] as String,
        createdAt: DateTime.parse(maps[i]['createdAt'] as String),
      );
    });
  }
}
```

---

## Data Management and Synchronization

1.  **Local First:** All generated content is immediately saved to the local SQLite database. This ensures offline access.
2.  **Sync Queue:** If a cloud-based generation is requested while offline, the request parameters are saved to a separate "sync queue" table in the local database.
3.  **Connectivity Listener:** A service using a package like `connectivity_plus` listens for changes in network status.
4.  **Background Sync:** When connectivity is restored, a background process (using `flutter_workmanager` or similar) iterates through the sync queue, sends the requests to the Gemini API, and updates the local database with the results.

---

## Necessary Permissions

The `AndroidManifest.xml` (for Android) and `Info.plist` (for iOS) would need to be updated to include:

*   **Internet:** To connect to the Gemini API.
    *   Android: `<uses-permission android:name="android.permission.INTERNET" />`
    *   iOS: No specific entry needed for basic internet access, but App Transport Security might need configuration.
*   **Microphone:** For voice input features.
    *   Android: `<uses-permission android:name="android.permission.RECORD_AUDIO" />`
    *   iOS: `NSMicrophoneUsageDescription` (with a clear explanation for the user).
*   **Network State:** To check for connectivity.
    *   Android: `<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />`

---

## Recommendations

*   **Framework:** Flutter is an excellent choice due to its cross-platform nature, strong performance, and rich ecosystem of packages that support AI and offline capabilities.
*   **On-Device AI:** For on-device inference with Gemini Nano, you would use a platform-specific integration (e.g., via platform channels in Flutter) to call the native ML libraries (like Google AI Edge for Android). This is a more advanced topic that would require native code development.
