# from django.contrib.gis.db import models as gis_models  # Temporarily disabled
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class AttendanceGroup(models.Model):
    """
    Attendance groups define locations and schedules for employee check-ins.
    Uses GeoDjango for efficient location-based queries and validation.
    """
    name = models.CharField(
        max_length=100,
        help_text="Name of the attendance group (e.g., 'Main Office', 'Warehouse')"
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='attendance_groups',
        help_text="Company this attendance group belongs to"
    )
    branch = models.ForeignKey(
        'companies.Branch',
        on_delete=models.CASCADE,
        related_name='attendance_groups',
        null=True,
        blank=True,
        help_text="Branch this attendance group is associated with"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the attendance group"
    )
    # Store location using latitude/longitude fields (will upgrade to GeoDjango later)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Latitude coordinate for check-in validation"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Longitude coordinate for check-in validation"
    )
    # Radius in meters for valid check-ins
    radius = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(10), MaxValueValidator(5000)],
        help_text="Radius in meters within which employees can check in"
    )
    # Employees assigned to this attendance group
    employees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='AttendanceGroupMembership',
        related_name='attendance_groups',
        blank=True,
        help_text="Employees assigned to this attendance group"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this attendance group is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendance_attendancegroup'
        verbose_name = 'Attendance Group'
        verbose_name_plural = 'Attendance Groups'
        ordering = ['company', 'name']
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"
    
    def is_within_radius(self, user_lat, user_lon):
        """
        Check if a given location is within the allowed radius.
        Args:
            user_lat: User's latitude
            user_lon: User's longitude
        Returns:
            bool: True if within radius, False otherwise
        """
        from math import radians, cos, sin, asin, sqrt
        
        # Haversine formula to calculate distance between two points
        def haversine(lon1, lat1, lon2, lat2):
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371000  # Radius of earth in meters
            return c * r
        
        distance = haversine(
            float(self.longitude), float(self.latitude),
            user_lon, user_lat
        )
        return distance <= self.radius
    
    @property
    def active_employee_count(self):
        """Get number of active employees in this group"""
        return self.attendancegroupmembership_set.filter(
            is_active=True,
            employee__is_active=True
        ).count()


class AttendanceGroupMembership(models.Model):
    """
    Through model for AttendanceGroup-Employee many-to-many relationship.
    Tracks when employees are assigned/removed from attendance groups.
    """
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="Employee assigned to the attendance group"
    )
    attendance_group = models.ForeignKey(
        AttendanceGroup,
        on_delete=models.CASCADE,
        help_text="Attendance group the employee is assigned to"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this assignment is currently active"
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the employee was assigned to this group"
    )
    removed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the employee was removed from this group"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendance_attendancegroupmembership'
        verbose_name = 'Attendance Group Membership'
        verbose_name_plural = 'Attendance Group Memberships'
        # Ensure one active membership per employee per group
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'attendance_group'],
                name='unique_active_group_membership',
                condition=models.Q(is_active=True)
            )
        ]
    
    def __str__(self):
        return f"{self.employee.username} in {self.attendance_group.name}"
    
    def deactivate(self):
        """Deactivate this membership and set removed_at timestamp"""
        self.is_active = False
        self.removed_at = timezone.now()
        self.save()


class Period(models.Model):
    """
    Periods define work schedules/shifts for attendance groups.
    Each period has specific start/end times and applicable weekdays.
    """
    name = models.CharField(
        max_length=100,
        help_text="Period name (e.g., 'Morning Shift', 'Evening Shift')"
    )
    group = models.ForeignKey(
        AttendanceGroup,
        on_delete=models.CASCADE,
        related_name='periods',
        help_text="Attendance group this period belongs to"
    )
    start_time = models.TimeField(
        help_text="Period start time"
    )
    end_time = models.TimeField(
        help_text="Period end time"
    )
    # Store weekdays as comma-separated values: "1,2,3,4,5" for Mon-Fri
    weekdays = models.CharField(
        max_length=15,
        help_text="Applicable weekdays (1=Monday, 7=Sunday). Format: '1,2,3,4,5'"
    )
    # Grace periods for late check-in/early check-out
    late_checkin_grace_minutes = models.PositiveIntegerField(
        default=15,
        help_text="Grace period in minutes for late check-in"
    )
    early_checkout_grace_minutes = models.PositiveIntegerField(
        default=15,
        help_text="Grace period in minutes for early check-out"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this period is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendance_period'
        verbose_name = 'Period'
        verbose_name_plural = 'Periods'
        ordering = ['group', 'start_time']
    
    def __str__(self):
        return f"{self.group.name} - {self.name} ({self.start_time}-{self.end_time})"
    
    @property
    def weekday_list(self):
        """Get list of weekdays as integers"""
        return [int(day.strip()) for day in self.weekdays.split(',') if day.strip()]
    
    @property
    def weekday_names(self):
        """Get list of weekday names"""
        day_names = {
            1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday',
            5: 'Friday', 6: 'Saturday', 7: 'Sunday'
        }
        return [day_names[day] for day in self.weekday_list]
    
    def is_applicable_today(self):
        """Check if this period is applicable for today"""
        today_weekday = timezone.now().isoweekday()
        return today_weekday in self.weekday_list
    
    def is_within_checkin_time(self, check_time=None):
        """
        Check if given time is within check-in window (including grace period).
        Args:
            check_time: datetime object, defaults to now
        Returns:
            bool: True if within check-in window
        """
        if check_time is None:
            check_time = timezone.now()
        
        check_time_only = check_time.time()
        grace_start = (
            timezone.datetime.combine(timezone.now().date(), self.start_time) -
            timezone.timedelta(minutes=self.late_checkin_grace_minutes)
        ).time()
        
        return grace_start <= check_time_only <= self.end_time


class CheckIn(models.Model):
    """
    Individual check-in/check-out records for employees.
    Uses GeoDjango to store and validate location data.
    """
    class CheckInType(models.TextChoices):
        CHECK_IN = 'IN', 'Check-In'
        CHECK_OUT = 'OUT', 'Check-Out'
    
    class CheckInStatus(models.TextChoices):
        ON_TIME = 'ON_TIME', 'On Time'
        LATE = 'LATE', 'Late'
        EARLY = 'EARLY', 'Early'
        INVALID_LOCATION = 'INVALID_LOCATION', 'Invalid Location'
        INVALID_TIME = 'INVALID_TIME', 'Invalid Time'
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='checkins',
        help_text="Employee who made this check-in"
    )
    attendance_group = models.ForeignKey(
        AttendanceGroup,
        on_delete=models.CASCADE,
        related_name='checkins',
        help_text="Attendance group for this check-in"
    )
    period = models.ForeignKey(
        Period,
        on_delete=models.CASCADE,
        related_name='checkins',
        null=True,
        blank=True,
        help_text="Period this check-in is associated with"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the check-in was made"
    )
    # Store location using latitude/longitude fields (will upgrade to GeoDjango later)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Latitude where check-in was made"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Longitude where check-in was made"
    )
    type = models.CharField(
        max_length=3,
        choices=CheckInType.choices,
        help_text="Type of check-in (IN/OUT)"
    )
    status = models.CharField(
        max_length=20,
        choices=CheckInStatus.choices,
        default=CheckInStatus.ON_TIME,
        help_text="Status of the check-in"
    )
    # Distance from the attendance group location in meters
    distance_from_location = models.FloatField(
        null=True,
        blank=True,
        help_text="Distance in meters from the attendance group location"
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes or comments"
    )
    # IP address for additional security/tracking
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address from which check-in was made"
    )
    # User agent for device tracking
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string from the device"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendance_checkin'
        verbose_name = 'Check-In'
        verbose_name_plural = 'Check-Ins'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['employee', '-timestamp']),
            models.Index(fields=['attendance_group', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.employee.username} - {self.get_type_display()} at {self.timestamp}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate distance and validate location"""
        if self.latitude and self.longitude and self.attendance_group:
            # Calculate distance from attendance group location using Haversine formula
            from math import radians, cos, sin, asin, sqrt
            
            def haversine(lon1, lat1, lon2, lat2):
                lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                r = 6371000  # Radius of earth in meters
                return c * r
            
            distance = haversine(
                float(self.attendance_group.longitude), float(self.attendance_group.latitude),
                float(self.longitude), float(self.latitude)
            )
            self.distance_from_location = distance
            
            # Validate location and set status
            if not self.attendance_group.is_within_radius(float(self.latitude), float(self.longitude)):
                self.status = self.CheckInStatus.INVALID_LOCATION
            elif self.period and not self.period.is_within_checkin_time(self.timestamp):
                # Check if it's late or early
                check_time = self.timestamp.time()
                if check_time > self.period.end_time:
                    self.status = self.CheckInStatus.INVALID_TIME
                elif check_time > self.period.start_time:
                    self.status = self.CheckInStatus.LATE
                else:
                    self.status = self.CheckInStatus.EARLY
        
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """Check if this check-in is valid (correct location and time)"""
        return self.status not in [self.CheckInStatus.INVALID_LOCATION, self.CheckInStatus.INVALID_TIME]
    
    @property
    def company(self):
        """Get the company this check-in belongs to"""
        return self.attendance_group.company


class AttendanceSummary(models.Model):
    """
    Daily attendance summary for employees.
    Automatically generated to provide quick access to daily attendance data.
    """
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_summaries'
    )
    attendance_group = models.ForeignKey(
        AttendanceGroup,
        on_delete=models.CASCADE,
        related_name='attendance_summaries'
    )
    date = models.DateField(
        help_text="Date for this attendance summary"
    )
    first_checkin = models.ForeignKey(
        CheckIn,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='first_checkin_summaries',
        help_text="First check-in of the day"
    )
    last_checkout = models.ForeignKey(
        CheckIn,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_checkout_summaries',
        help_text="Last check-out of the day"
    )
    total_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Total hours worked"
    )
    total_checkins = models.PositiveIntegerField(
        default=0,
        help_text="Total number of check-ins for the day"
    )
    is_present = models.BooleanField(
        default=False,
        help_text="Whether employee was present this day"
    )
    is_late = models.BooleanField(
        default=False,
        help_text="Whether employee was late"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendance_attendancesummary'
        verbose_name = 'Attendance Summary'
        verbose_name_plural = 'Attendance Summaries'
        # Ensure one summary per employee per day per group
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'attendance_group', 'date'],
                name='unique_daily_attendance_summary'
            )
        ]
        ordering = ['-date', 'employee']
    
    def __str__(self):
        return f"{self.employee.username} - {self.date} ({self.total_hours}h)"
    
    @property
    def company(self):
        """Get the company this summary belongs to"""
        return self.attendance_group.company
