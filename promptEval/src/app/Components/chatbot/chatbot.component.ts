// components/chatbot/chatbot.component.ts
import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  AfterViewChecked,
} from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import {
  ChatbotService,
  ChatMessage,
  Conversation,
  ChatResponse,
} from '../../Service/chatbot.service';
import { Observable } from 'rxjs';
import { CommonModule, DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-chatbot',
  imports: [DecimalPipe, CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.css'],
})
export class ChatbotComponent implements OnInit, AfterViewChecked {
  @ViewChild('messageContainer') private messageContainer!: ElementRef;
  @ViewChild('messageInput') private messageInput!: ElementRef;

  // Form
  messageForm: FormGroup;

  // State
  activeConversation: Conversation | null = null;
  conversations: Conversation[] = [];
  isProcessing = false;
  showSidebar = true;
  showSources = false;
  knowledgeBaseStats: any = null;

  // Suggestions from last response
  currentSuggestions: string[] = [];
  currentSources: any[] = [];

  // Typing indicator
  isTyping = false;

  constructor(private fb: FormBuilder, private chatbotService: ChatbotService) {
    this.messageForm = this.fb.group({
      message: ['', [Validators.required, Validators.minLength(2)]],
    });
  }

  ngOnInit(): void {
    // Subscribe to active conversation
    this.chatbotService.activeConversation$.subscribe((conversation) => {
      this.activeConversation = conversation;
      this.scrollToBottom();
    });

    // Subscribe to conversations list
    this.chatbotService.conversations$.subscribe((conversations) => {
      this.conversations = conversations;
    });

    // Subscribe to loading state
    this.chatbotService.loading$.subscribe((loading) => {
      this.isProcessing = loading;
    });

    // Subscribe to knowledge base stats
    this.chatbotService.knowledgeBaseStats$.subscribe((stats) => {
      this.knowledgeBaseStats = stats;
    });

    // Load initial data
    this.loadInitialData();

    // Auto-focus input
    setTimeout(() => this.focusInput(), 100);
  }

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  // In chatbot.component.ts - Update the loadInitialData method
  loadInitialData(): void {
    // Check for saved active conversation
    const savedConversationId = localStorage.getItem('activeChatConversation');

    if (savedConversationId) {
      // Try to load the saved conversation
      this.chatbotService.getConversation(savedConversationId).subscribe({
        next: (conversation) => {
          // Success - conversation exists on backend
          console.log('Loaded saved conversation:', conversation.id);
        },
        error: (error) => {
          // If we get a 404, the conversation doesn't exist on backend
          console.warn(
            'Saved conversation not found on server, creating new one'
          );
          localStorage.removeItem('activeChatConversation'); // Clean up
          this.createNewChat(); // Start fresh
        },
      });
    } else if (this.conversations.length === 0) {
      // Create a new conversation
      this.createNewChat();
    }

    // Load knowledge base stats
    this.chatbotService.loadKnowledgeBaseStats().subscribe();
  }

  /**
   * Send a message
   */
  onSubmit(): void {
    if (this.messageForm.invalid || this.isProcessing) {
      return;
    }

    const message = this.messageForm.get('message')?.value;

    if (!this.activeConversation) {
      this.createNewChat();
    }

    // Send message
    this.chatbotService
      .sendMessage(message, this.activeConversation?.id)
      .subscribe({
        next: (response) => {
          this.currentSuggestions = response.suggestions;
          this.currentSources = response.sources;
          this.messageForm.reset();
          this.focusInput();
        },
        error: (error) => {
          console.error('Failed to send message:', error);
          // Add error message to chat
          if (this.activeConversation) {
            const errorMessage: ChatMessage = {
              role: 'assistant',
              content: 'Sorry, I encountered an error. Please try again.',
              timestamp: new Date(),
            };
            this.activeConversation.messages.push(errorMessage);
          }
        },
      });
  }

  /**
   * Create a new chat
   */
  createNewChat(): void {
    this.chatbotService.createNewConversation();
    this.currentSuggestions = [];
    this.currentSources = [];
    this.showSources = false;
    this.focusInput();
  }

  /**
   * Select a conversation
   */
  selectConversation(conversation: Conversation): void {
    this.chatbotService.setActiveConversation(conversation);
    this.currentSuggestions = [];
    this.currentSources = [];
    this.showSources = false;

    // Close sidebar on mobile
    if (window.innerWidth < 768) {
      this.showSidebar = false;
    }

    this.focusInput();
  }

  /**
   * Delete a conversation
   */
  deleteConversation(conversation: Conversation, event?: MouseEvent): void {
    if (event) {
      event.stopPropagation();
    }

    if (confirm('Are you sure you want to delete this conversation?')) {
      this.chatbotService.deleteConversation(conversation.id).subscribe();
    }
  }

  /**
   * Use a suggestion
   */
  useSuggestion(suggestion: string): void {
    this.messageForm.patchValue({ message: suggestion });
    this.onSubmit();
  }

  /**
   * Copy message to clipboard
   */
  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text).then(() => {
      // Show success toast
      console.log('Copied to clipboard');
    });
  }

  /**
   * Refresh knowledge base
   */
  refreshKnowledgeBase(): void {
    this.chatbotService.refreshKnowledgeBase().subscribe({
      next: () => {
        // Show success message
        console.log('Knowledge base refreshed');
      },
      error: (error) => {
        console.error('Failed to refresh knowledge base:', error);
      },
    });
  }

  /**
   * Format message time
   */
  formatTime(timestamp: any): string {
    return this.chatbotService.formatMessageTime(timestamp);
  }

  /**
   * Check if message is from user
   */
  isUserMessage(message: ChatMessage): boolean {
    return this.chatbotService.isUserMessage(message);
  }

  /**
   * Get conversation summary for display
   */
  getConversationSummary(conversation: Conversation): string {
    return this.chatbotService.getConversationSummary(conversation);
  }

  /**
   * Toggle sidebar
   */
  toggleSidebar(): void {
    this.showSidebar = !this.showSidebar;
  }

  /**
   * Toggle sources display
   */
  toggleSources(): void {
    this.showSources = !this.showSources;
  }

  /**
   * Scroll to bottom of message container
   */
  // In chatbot.component.ts - Fix the scrollToBottom method
  private scrollToBottom(): void {
    try {
      setTimeout(() => {
        if (this.messageContainer?.nativeElement) {
          const element = this.messageContainer.nativeElement;
          // Only scroll if we're near the bottom
          const isNearBottom =
            element.scrollHeight - element.scrollTop - element.clientHeight <
            100;

          if (isNearBottom) {
            element.scrollTop = element.scrollHeight;
          }
        }
      }, 100);
    } catch (err) {
      console.error('Scroll error:', err);
    }
  }

  // Add a method to manually scroll
  scrollManually(event: Event): void {
    // This can be called from a button or UI control
    const element = this.messageContainer?.nativeElement;
    if (element) {
      element.scrollTop = 0; // Scroll to top
    }
  }

  /**
   * Focus the message input
   */
  private focusInput(): void {
    setTimeout(() => {
      if (this.messageInput) {
        this.messageInput.nativeElement.focus();
      }
    }, 100);
  }

  /**
   * Handle key press for sending with Enter
   */
  onKeyPress(event: any): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.onSubmit();
    }
  }

  /**
   * Check if knowledge base is ready
   */
  isKnowledgeBaseReady(): boolean {
    return this.knowledgeBaseStats?.status === 'ready';
  }
}
