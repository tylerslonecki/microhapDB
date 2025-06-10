# MicrohapDB Frontend

Vue.js frontend for the MicrohapDB database system.

## Recent Improvements (Timeout and Race Condition Fixes)

### DataUpload Component Enhancements

We've implemented significant improvements to handle timeout and race condition issues:

#### 1. Request Cancellation and Debouncing
- **AbortController Integration**: All API requests now use AbortController to allow cancellation
- **Debounced Requests**: 300ms debouncing prevents rapid-fire requests when users quickly switch between dropdowns
- **Request Deduplication**: Prevents multiple simultaneous requests for the same resource

#### 2. Enhanced Timeout Handling
- **Increased Timeouts**: 
  - Default: 15 seconds (was 10s)
  - Long operations: 45 seconds (was 30s)
  - File uploads: 60 seconds
  - Heavy operations: 120 seconds
- **Retry Logic**: Automatic retry with exponential backoff (2 retries with 1s, 2s delays)
- **Graceful Degradation**: Provides fallback options when requests fail

#### 3. Improved User Experience
- **Loading Indicators**: Visual feedback during API requests
- **Error States**: Clear error messages for timeout and network issues
- **Disabled States**: Prevents user interaction during loading
- **Status Messages**: Real-time feedback on request progress

#### 4. Better Error Handling
- **Network Error Detection**: Distinguishes between timeout and network errors
- **User-Friendly Messages**: Converts technical errors to readable messages
- **Recovery Options**: Provides guidance for resolving issues

### Key Files Modified
- `DataUpload.vue`: Main component with enhanced request handling
- `axiosConfig.js`: Improved timeout configuration and error handling
- Added loading states and visual indicators

### Usage Notes
- Dropdown loading is now properly handled with visual feedback
- Users can safely switch between species without causing request conflicts
- Network issues are clearly communicated with actionable error messages
- The system automatically retries failed requests before giving up
- **PAV Upload**: Only allows selection of existing programs (no "Add new program" option)
- **MADC Upload**: Allows both selection of existing programs and creation of new programs and projects

### Testing
To test the improvements:
1. Run the development server: `npm run serve`
2. Navigate to the Data Upload page
3. Try rapidly switching between species in dropdowns
4. Observe the loading indicators and improved error handling

## Project setup
```
npm install
```

### Compiles and hot-reloads for development
```
npm run serve
```

### Compiles and minifies for production
```
npm run build
```

### Lints and fixes files
```
npm run lint
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).
