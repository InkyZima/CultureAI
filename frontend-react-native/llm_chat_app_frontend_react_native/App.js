import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, Text, View, TextInput, Button, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import axios from 'axios';

const BACKEND_URL = Platform.OS === 'android' ? 'http://127.0.0.1:5000' : 'http://localhost:5000'; // Adjust for Android emulator

export default function App() {
    const [chatHistory, setChatHistory] = useState([]);
    const [userMessage, setUserMessage] = useState('');
    const scrollViewRef = useRef();

    useEffect(() => {
        fetchChatHistory();
    }, []);

    const fetchChatHistory = async () => {
        try {
            const response = await axios.get(`${BACKEND_URL}/chat_history`);
            if (response.status === 200) {
                setChatHistory(response.data.history);
            } else {
                console.error("Failed to fetch chat history:", response.status, response.statusText);
            }
        } catch (error) {
            console.error("Error fetching chat history:", error);
        }
    };

    const handleSendMessage = async () => {
        if (!userMessage.trim()) return;

        const messageToSend = userMessage.trim();
        setUserMessage(''); // Clear input immediately

        try {
          console.log("Sending message.");
            const response = await axios.post(`${BACKEND_URL}/chat`, { message: messageToSend });
            if (response.status === 200) {
                // Optimistically update chat history - could also refetch for guaranteed sync
                setChatHistory(prevHistory => [...prevHistory, { user_message: messageToSend, llm_response: response.data.response }]);
            } else {
                console.error("Failed to send message:", response.status, response.statusText);
                // Revert optimistic update or handle error in UI
            }
        } catch (error) {
            console.error("Error sending message:", error);
            // Handle error in UI (e.g., display error message to user)
        }
    };

    useEffect(() => {
        // Scroll to bottom of chat on new messages
        scrollViewRef.current?.scrollToEnd({ animated: true });
    }, [chatHistory]);


    return (
        <KeyboardAvoidingView
            behavior={Platform.OS === "ios" ? "padding" : "height"}
            style={{flex: 1}}
        >
            <View style={styles.container}>
                <ScrollView style={styles.chatWindow} contentContainerStyle={styles.chatWindowContent} ref={scrollViewRef}>
                    {chatHistory.map((message, index) => (
                        <View key={index} style={styles.messageContainer}>
                            {message.user_message && (
                                <View style={styles.userMessageBubble}>
                                    <Text style={styles.messageText}>{message.user_message}</Text>
                                </View>
                            )}
                            {message.llm_response && (
                                <View style={styles.llmMessageBubble}>
                                    <Text style={styles.messageText}>{message.llm_response}</Text>
                                </View>
                            )}
                        </View>
                    ))}
                </ScrollView>

                <View style={styles.inputArea}>
                    <TextInput
                        style={styles.input}
                        placeholder="Type your message..."
                        value={userMessage}
                        onChangeText={setUserMessage}
                        onSubmitEditing={handleSendMessage} // Send message on pressing 'Enter' (on some keyboards)
                        returnKeyType="send"
                        blurOnSubmit={false} // Keep input focused after submit
                    />
                    <Button
                        title="Send"
                        onPress={handleSendMessage}
                        style={styles.sendButton}
                    />
                </View>
            </View>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
    },
    chatWindow: {
        flex: 1,
        padding: 10,
    },
    chatWindowContent: {
        paddingBottom: 20, // Add some padding at the bottom for scrolling
    },
    messageContainer: {
        marginBottom: 10,
    },
    userMessageBubble: {
        backgroundColor: '#DCF8C6', // Light green for user messages
        padding: 10,
        borderRadius: 10,
        alignSelf: 'flex-end', // Align user messages to the right
        maxWidth: '80%',
    },
    llmMessageBubble: {
        backgroundColor: '#f0f0f0', // Light gray for LLM messages
        padding: 10,
        borderRadius: 10,
        alignSelf: 'flex-start', // Align LLM messages to the left
        maxWidth: '80%',
    },
    messageText: {
        fontSize: 16,
    },
    inputArea: {
        flexDirection: 'row',
        padding: 10,
        borderTopWidth: 1,
        borderTopColor: '#ccc',
        alignItems: 'center', // Vertically align input and button
    },
    input: {
        flex: 1,
        padding: 8,
        borderWidth: 1,
        borderColor: '#ccc',
        borderRadius: 5,
        marginRight: 8,
    },
    sendButton: {
        marginLeft: 8,
    },
});