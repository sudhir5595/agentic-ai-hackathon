import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:image_picker/image_picker.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:google_mlkit_translation/google_mlkit_translation.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MedIntelliCare',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: Colors.black,
        textTheme: const TextTheme(
          bodyMedium: TextStyle(color: Colors.white),
        ),
      ),
      home: const ChatScreen(),
    );
  }
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final List<Map<String, String>> _messages = [];
  late stt.SpeechToText _speech;
  late OnDeviceTranslator _translatorToEnglish;
  late OnDeviceTranslator _translatorFromEnglish;
  final ImagePicker _picker = ImagePicker();
  bool _isListening = false;
  String _text = '';
  Locale _selectedLocale = const Locale('en');

  @override
  void initState() {
    super.initState();
    _speech = stt.SpeechToText();
    _initializeTranslators();
  }

  void _initializeTranslators() {
    _translatorToEnglish = OnDeviceTranslator(
      sourceLanguage: _getMLKitLanguage(_selectedLocale.languageCode),
      targetLanguage: TranslateLanguage.english,
    );
    _translatorFromEnglish = OnDeviceTranslator(
      sourceLanguage: TranslateLanguage.english,
      targetLanguage: _getMLKitLanguage(_selectedLocale.languageCode),
    );
  }

  TranslateLanguage _getMLKitLanguage(String languageCode) {
    switch (languageCode) {
      case 'hi':
        return TranslateLanguage.hindi;
      case 'ta':
        return TranslateLanguage.tamil;
      case 'te':
        return TranslateLanguage.telugu;
      case 'mr':
        return TranslateLanguage.marathi;
      default:
        return TranslateLanguage.english;
    }
  }

  void _setLocale(Locale locale) {
    setState(() {
      _selectedLocale = locale;
      _initializeTranslators();
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    _translatorToEnglish.close();
    _translatorFromEnglish.close();
    super.dispose();
  }

  // Function to send messages to the backend
  void _sendMessage(String message) async {
    setState(() {
      _messages.add({"role": "user", "content": message});
    });

    try {
      // Translate user input to English
      final translatedMessage =
          await _translatorToEnglish.translateText(message);

      // Send the translated message to the backend
      final response = await http.post(
        Uri.parse(
            'http://192.168.55.200:5000/chat'), // Replace with backend URL
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': translatedMessage}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        // Translate the response from English to the user's language
        final translatedResponse = await _translatorFromEnglish
            .translateText(data['answer'] ?? "No response");

        setState(() {
          _messages.add({"role": "assistant", "content": translatedResponse});
        });
      } else {
        setState(() {
          _messages.add({
            "role": "assistant",
            "content": "Error: Unable to get response."
          });
        });
      }
    } catch (e) {
      setState(() {
        _messages.add({
          "role": "assistant",
          "content": "Error: Unable to connect to the server."
        });
      });
    }

    _controller.clear();
  }

  // Voice input methods
  void _startListening() async {
    bool available = await _speech.initialize(
      onStatus: (val) => print('onStatus: $val'),
      onError: (val) => print('onError: $val'),
    );
    if (available) {
      setState(() => _isListening = true);
      _speech.listen(
        onResult: (val) => setState(() {
          _text = val.recognizedWords;
        }),
      );
    }
  }

  void _stopListening() {
    setState(() => _isListening = false);
    _speech.stop();
    if (_text.isNotEmpty) {
      _sendMessage(_text);
    }
  }

  // Image input method with OCR
  void _pickImage() async {
    final pickedFile = await _picker.pickImage(source: ImageSource.gallery);

    if (pickedFile != null) {
      // Display a placeholder message while analyzing the report
      setState(() {
        _messages
            .add({"role": "assistant", "content": "Analyzing the report..."});
      });

      File imageFile = File(pickedFile.path);

      // Extract text from image using OCR
      final extractedText = await _extractTextFromImage(imageFile);

      if (extractedText.isNotEmpty) {
        // Directly send the extracted text to the backend without adding it as a user message
        await _sendMessageToBackend(extractedText);
      } else {
        setState(() {
          _messages.add({
            "role": "assistant",
            "content": "No text detected in the image."
          });
        });
      }
    }
  }

  Future<void> _sendMessageToBackend(String extractedText) async {
    try {
      // Send the extracted text directly to the backend
      final translatedMessage =
          await _translatorToEnglish.translateText(extractedText);

      final response = await http.post(
        Uri.parse('http://192.168.1.10:5000/chat'), // Replace with backend URL
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': translatedMessage}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        // Translate the response from English to the user's language
        final translatedResponse = await _translatorFromEnglish
            .translateText(data['answer'] ?? "No response");

        setState(() {
          _messages.removeLast(); // Remove the placeholder message
          _messages.add({"role": "assistant", "content": translatedResponse});
        });
      } else {
        setState(() {
          _messages.removeLast(); // Remove the placeholder message
          _messages.add({
            "role": "assistant",
            "content": "Error: Unable to get response from the server."
          });
        });
      }
    } catch (e) {
      setState(() {
        _messages.removeLast(); // Remove the placeholder message
        _messages.add({
          "role": "assistant",
          "content": "Error: Unable to connect to the server."
        });
      });
    }
  }

  // Function to perform OCR and extract text
  Future<String> _extractTextFromImage(File imageFile) async {
    final inputImage = InputImage.fromFile(imageFile);
    final textRecognizer = TextRecognizer();
    final RecognizedText recognizedText =
        await textRecognizer.processImage(inputImage);
    await textRecognizer.close();

    return recognizedText.text;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('MedIntelliCare'),
        actions: [
          DropdownButton<Locale>(
            value: _selectedLocale,
            onChanged: (Locale? newLocale) {
              if (newLocale != null) {
                _setLocale(newLocale);
              }
            },
            items: const [
              DropdownMenuItem(value: Locale('en'), child: Text("English")),
              DropdownMenuItem(value: Locale('hi'), child: Text("हिंदी")),
              DropdownMenuItem(value: Locale('ta'), child: Text("தமிழ்")),
              DropdownMenuItem(value: Locale('te'), child: Text("తెలుగు")),
              DropdownMenuItem(
                  value: Locale('mr'), child: Text("मराठी")), // Marathi option
            ],
          ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 600),
          child: Column(
            children: [
              Expanded(
                child: ListView.builder(
                  itemCount: _messages.length,
                  itemBuilder: (context, index) {
                    final message = _messages[index];
                    return Align(
                      alignment: message['role'] == 'user'
                          ? Alignment.centerRight
                          : Alignment.centerLeft,
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            vertical: 5, horizontal: 10),
                        margin: const EdgeInsets.symmetric(
                            vertical: 5, horizontal: 20),
                        decoration: BoxDecoration(
                          color: message['role'] == 'user'
                              ? Colors.blue
                              : Colors.grey[800],
                          borderRadius: BorderRadius.circular(15),
                        ),
                        child: MarkdownBody(
                          data: message['content'] ?? "No content",
                          styleSheet: MarkdownStyleSheet(
                            p: const TextStyle(color: Colors.white),
                            strong:
                                const TextStyle(fontWeight: FontWeight.bold),
                            em: const TextStyle(fontStyle: FontStyle.italic),
                            a: const TextStyle(
                                color: Colors.blue,
                                decoration: TextDecoration.underline),
                          ),
                          onTapLink: (text, href, title) {
                            if (href != null) {
                              _launchURL(href);
                            }
                          },
                        ),
                      ),
                    );
                  },
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(8.0),
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.image),
                      onPressed: _pickImage,
                      color: Colors.blue,
                    ),
                    Expanded(
                      child: TextField(
                        controller: _controller,
                        onSubmitted: (value) {
                          if (value.isNotEmpty) {
                            _sendMessage(value);
                          }
                        },
                        decoration: InputDecoration(
                          hintText: 'Type your message...',
                          hintStyle: const TextStyle(color: Colors.white54),
                          filled: true,
                          fillColor: Colors.grey[900],
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(20.0),
                          ),
                        ),
                        style: const TextStyle(color: Colors.white),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.send),
                      onPressed: () {
                        if (_controller.text.isNotEmpty) {
                          _sendMessage(_controller.text);
                        }
                      },
                      color: Colors.blue,
                    ),
                    IconButton(
                      icon: Icon(_isListening ? Icons.mic : Icons.mic_none),
                      onPressed:
                          _isListening ? _stopListening : _startListening,
                      color: Colors.blue,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _launchURL(String url) async {
    if (await canLaunch(url)) {
      await launch(url);
    } else {
      throw 'Could not launch $url';
    }
  }
}
