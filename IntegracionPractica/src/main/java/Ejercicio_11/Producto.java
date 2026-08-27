package Ejercicio_11;

import java.util.Objects;

public class Producto {
    private String nombre;
    private double precioVenta;

    public Producto(String nombre, double precioVenta) {
        Objects.requireNonNull(nombre, "El nombre del producto no puede ser nulo");
        if (precioVenta <= 0) {
            throw new IllegalArgumentException("El precio de venta debe ser mayor a 0");
        }
        this.nombre = nombre;
        this.precioVenta = precioVenta;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        Objects.requireNonNull(nombre, "El nombre del producto no puede ser nulo");
        this.nombre = nombre;
    }

    public double getPrecioVenta() {
        return precioVenta;
    }

    public void setPrecioVenta(double precioVenta) {
        if (precioVenta <= 0) {
            throw new IllegalArgumentException("El precio de venta debe ser mayor a 0");
        }
        this.precioVenta = precioVenta;
    }
}
