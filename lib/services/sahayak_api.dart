import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:googleapis_auth/auth_io.dart';

/// Sahayak API Service for Deployed ADK Agent
class SahayakApi {
  // CONFIGURATION
  static const String _projectId = 'formidable-feat-466408-r6';
  static const String _location = 'us-central1';
  static const String _engineId = '7395007345165598720';
  static const String _serviceAccountPath = 'assets/google-credentials.json';

  // PRIVATE VARIABLES
  static String? _cachedAccessToken;
  static DateTime? _tokenExpiry;
  static const Duration _tokenRefreshBuffer = Duration(minutes: 5);
  static String? _currentSessionId;

  /// Check if current token is still valid
  static bool get _isTokenValid {
    return _cachedAccessToken != null &&
        _tokenExpiry != null &&
        DateTime.now().isBefore(_tokenExpiry!.subtract(_tokenRefreshBuffer));
  }

  /// Get valid access token (refresh if needed)
  static Future<String> _getAccessToken() async {
    if (_isTokenValid) {
      return _cachedAccessToken!;
    }

    try {
      final serviceAccountJson =
          await rootBundle.loadString(_serviceAccountPath);
      final credentials =
          ServiceAccountCredentials.fromJson(serviceAccountJson);

      final client = await clientViaServiceAccount(
        credentials,
        ['https://www.googleapis.com/auth/cloud-platform'],
      );

      _cachedAccessToken = client.credentials.accessToken.data;
      _tokenExpiry = client.credentials.accessToken.expiry;

      client.close();

      print('✅ Access token obtained successfully');
      return _cachedAccessToken!;
    } catch (e) {
      print('❌ Error getting access token: $e');
      throw Exception('Failed to authenticate: $e');
    }
  }

  /// Build endpoint URLs for different operations
  static Uri _buildStreamQueryEndpoint() {
    return Uri.https(
      '$_location-aiplatform.googleapis.com',
      '/v1/projects/$_projectId/locations/$_location/reasoningEngines/$_engineId:streamQuery',
      {'alt': 'sse'}, // Server-Sent Events for streaming
    );
  }

  static Uri _buildQueryEndpoint() {
    return Uri.https(
      '$_location-aiplatform.googleapis.com',
      '/v1/projects/$_projectId/locations/$_location/reasoningEngines/$_engineId:query',
    );
  }

  /// Create session using the deployed ADK agent
  static Future<String> _createSession(String userId) async {
    try {
      final accessToken = await _getAccessToken();
      final endpoint = _buildQueryEndpoint();

      print('🔄 Creating session with deployed ADK agent...');

      final response = await http.post(
        endpoint,
        headers: {
          'Authorization': 'Bearer $accessToken',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'class_method': 'create_session',
          'input': {
            'user_id': userId,
          }
        }),
      );

      print('📡 Session creation response status: ${response.statusCode}');
      print('📄 Session creation response: ${response.body}');

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);

        String? sessionId;
        if (responseData['output'] != null &&
            responseData['output']['id'] != null) {
          sessionId = responseData['output']['id'].toString();
        }

        if (sessionId == null || sessionId.isEmpty) {
          throw Exception('Session ID not found in response: ${response.body}');
        }

        _currentSessionId = sessionId;
        print('✅ Session created successfully: $_currentSessionId');
        return _currentSessionId!;
      } else {
        throw Exception(
            'Failed to create session: ${response.statusCode} ${response.body}');
      }
    } catch (e) {
      print('❌ Session creation failed: $e');
      throw Exception('Failed to create session: $e');
    }
  }

  /// Send message using stream_query (matching your curl example)
  static Future<String> _sendStreamQuery(
      String? sessionId, String message, String userId) async {
    try {
      final accessToken = await _getAccessToken();
      final endpoint = _buildStreamQueryEndpoint();

      print('🔄 Sending stream query to deployed ADK agent...');
      print(
          '📝 Message: ${message.length > 50 ? message.substring(0, 50) + '...' : message}');

      // Build request body exactly like your working curl example
      final Map<String, dynamic> requestBody = {
        'class_method': 'stream_query',
        'input': <String, dynamic>{
          'user_id': userId,
          'message': message,
        },
      };

// Now cast the nested 'input' to a Map before mutating it:
      final inputMap = requestBody['input'] as Map<String, dynamic>;
      inputMap['session_id'] = sessionId;

      print('📝 Request body: ${jsonEncode(requestBody)}');

      final response = await http.post(
        endpoint,
        headers: {
          'Authorization': 'Bearer $accessToken',
          'Content-Type': 'application/json',
        },
        body: jsonEncode(requestBody),
      );

      print('📡 Stream query response status: ${response.statusCode}');

      if (response.statusCode == 200) {
        final responseBody = response.body;
        print('✅ Stream query successful');
        print(
            '📄 Raw response: ${responseBody.length > 200 ? responseBody.substring(0, 200) + '...' : responseBody}');

        // Handle Server-Sent Events format
        if (responseBody.startsWith('data: ')) {
          // Parse SSE format
          final lines = responseBody.split('\n');
          final buffer = StringBuffer();

          for (final line in lines) {
            if (line.startsWith('data: ')) {
              final data = line.substring(6);
              if (data != '[DONE]' && data.isNotEmpty) {
                try {
                  final jsonData = jsonDecode(data);
                  if (jsonData['content'] != null) {
                    buffer.write(jsonData['content']);
                  } else if (jsonData['output'] != null) {
                    buffer.write(jsonData['output']);
                  }
                } catch (e) {
                  // Skip malformed JSON
                  print('⚠️ Skipping malformed SSE data: $data');
                }
              }
            }
          }

          final result = buffer.toString();
          return result.isEmpty ? 'No content in streaming response.' : result;
        } else {
          // Handle regular JSON response
          try {
            final responseData = jsonDecode(responseBody);
            if (responseData['output'] != null) {
              return responseData['output'].toString();
            } else {
              return responseBody;
            }
          } catch (e) {
            return responseBody.isEmpty
                ? 'Empty response from agent.'
                : responseBody;
          }
        }
      } else {
        print('❌ Stream query error: ${response.body}');
        throw Exception(
            'Stream query failed: ${response.statusCode} ${response.body}');
      }
    } catch (e) {
      print('❌ Stream query failed: $e');
      throw Exception('Failed to send stream query: $e');
    }
  }

  /// Main method to send message (simplified for ADK agents)
  static Future<String> ask(String message, {String? userId}) async {
    try {
      final finalUserId =
          userId ?? 'teacher-${DateTime.now().millisecondsSinceEpoch}';

      // Try to send message with current session (or let agent create one)
      return await _sendStreamQuery(_currentSessionId, message, finalUserId);
    } catch (e) {
      print('❌ Request failed: $e');
      throw Exception('Failed to communicate with ADK Agent: $e');
    }
  }

  /// Start a new conversation by clearing session
  static void startNewConversation() {
    _currentSessionId = null;
    print('🔄 Started new conversation');
  }

  /// Test connection by sending a simple message
  static Future<bool> testConnection() async {
    try {
      final userId = 'test-${DateTime.now().millisecondsSinceEpoch}';
      final response =
          await ask('Hello, this is a connection test.', userId: userId);
      print('✅ Connection test successful');
      return response.isNotEmpty && !response.toLowerCase().contains('error');
    } catch (e) {
      print('❌ Connection test failed: $e');
      return false;
    }
  }

  /// Clear cached data
  static void clearAuth() {
    _cachedAccessToken = null;
    _tokenExpiry = null;
    _currentSessionId = null;
    print('🔄 Cache cleared');
  }
}
