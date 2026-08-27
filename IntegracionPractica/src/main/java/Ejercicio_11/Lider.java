package Ejercicio_11;

import java.util.Date;
import java.util.Objects;

public class Lider extends RepresentanteVentas {
    private Date fechaPromocionLider;
    private Equipo equipo; // Asociación 1 — 1 Equipo

    public Lider(String nombre, String direccion, String telefono, Date fechaNacimiento,
                 String cuil, Date fechaIncorporacion, double porcentajeComision, 
                 Date fechaPromocionLider, Equipo equipo) {
        super(nombre, direccion, telefono, fechaNacimiento, cuil, fechaIncorporacion, porcentajeComision);
        Objects.requireNonNull(fechaPromocionLider, "La fecha de promoción a líder no puede ser nula");
        Objects.requireNonNull(equipo, "El equipo no puede ser nulo");
        this.fechaPromocionLider = fechaPromocionLider;
        this.equipo = equipo;
        this.equipo.setLider(this); // Mantener consistencia bidireccional
    }

    @Override
    public double calcularComision(Date fechaDesde) {
        // Comisión sobre ventas propias
        double comisionPropia = super.calcularComision(fechaDesde);

        // Comisión sobre ventas de los vendedores del equipo
        double ventasEquipo = 0.0;
        if (equipo != null && equipo.getVendedores() != null) {
            for (Vendedor v : equipo.getVendedores()) {
                double ventasVendedor = v.getTickets().stream()
                        .filter(t -> t.getFecha().after(fechaDesde) || t.getFecha().equals(fechaDesde))
                        .mapToDouble(TicketVenta::getPrecio)
                        .sum();
                ventasEquipo += ventasVendedor;
            }
        }
        double comisionEquipo = ventasEquipo * getPorcentajeComision();

        return comisionPropia + comisionEquipo;
    }

    public Date getFechaPromocionLider() {
        return fechaPromocionLider;
    }

    public void setFechaPromocionLider(Date fechaPromocionLider) {
        Objects.requireNonNull(fechaPromocionLider, "La fecha de promoción no puede ser nula");
        this.fechaPromocionLider = fechaPromocionLider;
    }

    public Equipo getEquipo() {
        return equipo;
    }

    public void setEquipo(Equipo equipo) {
        Objects.requireNonNull(equipo, "El equipo no puede ser nulo");
        this.equipo = equipo;
    }
}
